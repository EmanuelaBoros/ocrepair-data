#!/usr/bin/env python3
"""Ask an OpenAI model to correct the REFERENCE transcriptions of all train units, following ANNOTATION.md.

It uses the same instructions and the same safety checks as the viewer's "Correct whole unit (LLM)" button, and writes the result as a corrections file that
apply_ref_corrections.py can read (edited references only; nothing is marked "fully corrected", because that is the human annotator's decision).

  dry run (default, no API call, shows how many units and characters would be sent):
      python3 viewers/llm_correct_refs.py
  real run (needs OPENAI_API_KEY in the environment; the key is never written to a file):
      python3 viewers/llm_correct_refs.py --run --model gpt-6-luna --effort medium --out corrections/v1.1-llm_ref-corrections.json
  one language only (all its collections), e.g. French:
      python3 viewers/llm_correct_refs.py --run --lang fr
  second pass over units already done, for leftover line-end hyphens (destina-tions):
      python3 viewers/llm_correct_refs.py --run --hyphens --lang fr
  one collection, first 20 units, as a test:
      python3 viewers/llm_correct_refs.py --run --only icdar2017/en --max-units 20
  then:
      python3 viewers/apply_ref_corrections.py corrections/v1.1-llm_ref-corrections.json

After a change of the rules, `--revalidate` re-checks the edits already saved (no API call).
The run can be stopped and started again: units that are already in --out are skipped. Every unit costs one request.
"""
import argparse, concurrent.futures as cf, glob, json, os, re, sys, threading, time, urllib.error, urllib.request
try:
    from tqdm import tqdm
except ImportError:   # pip install tqdm for the progress bar; without it the script still works
    sys.exit("tqdm is not installed: pip install tqdm")

RULES = """You check the reference (ground-truth) transcription of a historical document that is used to evaluate OCR post-correction. Propose only corrections of clear, certain errors in the REFERENCE text, such as a typo, a swapped or missing letter, or a missing space after punctuation.
Strict rules:
- Be conservative. If you are not sure, propose nothing. An empty list is a good answer.
- Do not add words. Do not delete words.
- Do not modernise or normalise anything. Keep historical spellings, archaic and dialect forms, long s, ligatures, diacritics and combining accents, capitalisation, abbreviations and the punctuation habits of the period, even where they look wrong today.
- Do not add quotation marks or any other quotes, and do not change existing ones.
- Do not change numbers, names or dates unless the OCR text clearly shows that the reference has a typo.
- Do not touch line breaks, with one exception: a hyphen followed by a line break inside one word, left over from hyphenation at the end of a line (for example "re-" + line break + "ported"), is removed together with the line break, so that the word is whole ("reported"). Do not touch hyphens that belong to the text: compounds and fixed forms (vingt-deux, est-ce, ci-dessus, to-day, well-known), names, and dashes. Exception: a hyphen that is only a leftover of hyphenation at the end of a line, in the middle of one word, must be removed so that the word is whole (for example "destina-tions" becomes "destinations", "pro-curera" becomes "procurera", "con-dition" becomes "condition"). Then "find" is the broken word and "replace" the whole word; change nothing else in it.
Reply with JSON only: {"edits":[{"find":"...","replace":"...","reason":"...","confidence":"high|medium|low"}]}. "find" must be copied exactly from the reference, must occur exactly once in it, and should be as short as possible (a word, or a few characters with the neighbouring letters if needed)."""

ICDAR_EXCEPTION = """
Exception for this document (an ICDAR collection): in the reference, a line break sometimes falls in the middle of a word (for example "exam" + line break + "ple"). Remove that line break so that the word is whole ("example"): "find" is the word with its line break, "replace" is the whole word. Delete only the line break, add no space and no hyphen. A line break between two words stays. If the break splits a word together with a hyphen ("destina-" + line break + "tions"), remove both, so that the word is whole ("destinations")."""

WORD_HYPHEN = re.compile(r"[^\W\d_]-\n?[^\W\d_]")   # a hyphen between two letters (also across a line break)
QUOTES = re.compile('["“”„«»]')


def user_input(ref, ocr):
    return ("REFERENCE TEXT:\n" + ref + "\n\nOCR TEXT (noisy; for comparison only, do not copy its errors):\n" + ocr +
            '\n\nReply with JSON only, in the format {"edits":[{"find":"...","replace":"...","reason":"...","confidence":"high|medium|low"}]}. Use {"edits":[]} if nothing needs correcting.')


def validate(edits, text, icdar):
    """The viewer's checks: the text must be found exactly once, no word added, no quotation mark added, no hyphen added and none removed together with a change of letters, no line break touched (except the ICDAR rule)."""
    ok, bad = [], []
    for e in edits:
        f, r = str(e.get("find") or ""), str(e.get("replace") if e.get("replace") is not None else "")
        why = ""
        if not f or f == r: why = "no change"
        else:
            n = text.count(f)
            if n == 0: why = "text not found in the reference"
            elif n > 1: why = "text occurs %d times (ambiguous)" % n
            elif len(r.split()) > len(f.split()) and re.sub(r"\s+", "", r) != re.sub(r"\s+", "", f): why = "adds a word"   # as in the viewer: only a change of letters counts; a space added (a missing space after punctuation, glued words) is allowed
            elif len(QUOTES.findall(r)) > len(QUOTES.findall(f)): why = "adds a quotation mark"
            elif r.count("-") > f.count("-"): why = "adds a hyphen"
            elif r.count("-") < f.count("-") and re.sub(r"[-\s]", "", r) != re.sub(r"[-\s]", "", f): why = "changes letters while removing a hyphen"   # removing a leftover line-end hyphen (destina-tions) is wanted, but only that
            elif f.count("\n") != r.count("\n") and not (icdar and f.count("\n") > r.count("\n")) and r != f.replace("-\n", ""): why = "touches a line break"   # allowed in every collection: removing "-" + line break inside a word (re-\nported -> reported)
        (bad if why else ok).append({"find": f, "replace": r, "reason": str(e.get("reason") or ""),
                                     "confidence": e.get("confidence") if e.get("confidence") in ("high", "medium", "low") else "low", "rejected": why})
    return ok, bad


def apply_edits(text, ok):
    """Right to left, so that offsets stay valid; an edit that overlaps another one is skipped."""
    out, last, used, skipped = text, 10 ** 12, [], []
    for e in sorted(({**e, "at": text.index(e["find"])} for e in ok), key=lambda e: -e["at"]):
        if e["at"] + len(e["find"]) > last: skipped.append({**e, "rejected": "overlaps another edit"}); continue
        out = out[:e["at"]] + e["replace"] + out[e["at"] + len(e["find"]):]; last = e["at"]; used.append(e)
    return out, used[::-1], skipped


def ask(model, effort, key, ref, ocr, icdar, timeout=600, retries=4):
    body = json.dumps({"model": model, "reasoning": {"effort": effort}, "instructions": RULES + (ICDAR_EXCEPTION if icdar else ""),
                       "input": user_input(ref, ocr), "text": {"format": {"type": "json_object"}}}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request("https://api.openai.com/v1/responses", body, {"Content-Type": "application/json", "Authorization": "Bearer " + key})
            d = json.load(urllib.request.urlopen(req, timeout=timeout))
            raw = d.get("output_text") or "".join(c.get("text", "") for o in d.get("output", []) for c in o.get("content", []) if c.get("type") == "output_text")
            return json.loads(raw).get("edits", []), d.get("usage", {})
        except urllib.error.HTTPError as err:
            msg = err.read()[:300].decode("utf-8", "replace")
            if err.code in (401, 403, 404): sys.exit("API refused the request (HTTP %d): %s" % (err.code, msg))   # wrong key or model id: stop instead of retrying
            if attempt == retries - 1: raise RuntimeError("HTTP %d: %s" % (err.code, msg))
        except Exception as err:
            if attempt == retries - 1: raise RuntimeError(repr(err))
        time.sleep(5 * (attempt + 1))


def journal_append(path, out, src, did):
    """Append the finished unit as one line to the journal at once. The journal is never rewritten, so an overlapping run or a crash cannot erase it."""
    line = {"src": src, "did": did, "log": out["llm_log"][src][did], "edit": out["edits"].get(src, {}).get(did)}
    with open(path, "a", encoding="utf-8") as f: f.write(json.dumps(line, ensure_ascii=False) + "\n")


def load_journal(out, path):
    """Put every unit of the journal into `out` (a later line for the same unit wins). Returns the number of units read."""
    n = 0
    if not os.path.exists(path): return n
    for line in open(path, encoding="utf-8"):
        try: r = json.loads(line)
        except ValueError: continue   # a half-written last line
        out["llm_log"].setdefault(r["src"], {})[r["did"]] = r["log"]; n += 1
        if r.get("edit") is not None: out["edits"].setdefault(r["src"], {})[r["did"]] = r["edit"]
        else: out["edits"].get(r["src"], {}).pop(r["did"], None)
    return n


def load_union(first, folder, base="v1.1-llm_ref-corrections"):
    """All corrections of the folder in one dict: `first` (the dict of this run) wins, then every other file <base>*.json (one per language, e.g. _en, _fr) and its journal. Read only, nothing is written."""
    U = {"version": first.get("version", ""), "base": first.get("base", ""), "model": first.get("model", ""), "edits": {}, "corrected": {}, "discarded": {}, "llm_log": {}}
    srcs = [first]
    for f in sorted(glob.glob(os.path.join(folder, base + "*.json"))):
        if "backup" in f: continue
        try: d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError): continue
        load_journal(d, f.replace(".json", ".journal.jsonl")); srcs.append(d)
        U["model"] = U["model"] or d.get("model", "")
    for d in srcs:
        for src, units in d.get("llm_log", {}).items():
            for did, log in units.items():
                if did in U["llm_log"].setdefault(src, {}): continue
                U["llm_log"][src][did] = log
                if did in d.get("edits", {}).get(src, {}): U["edits"].setdefault(src, {})[did] = d["edits"][src][did]
    return U


def merge_from_disk(out, path):
    """Add to `out` the units that are in the file on disk but not in memory (done by a run that works on other units at the same time). Units we hold win."""
    try: disk = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError): return
    for src, units in disk.get("llm_log", {}).items():
        for did, log in units.items():
            if did not in out["llm_log"].setdefault(src, {}):
                out["llm_log"][src][did] = log
                if did in disk.get("edits", {}).get(src, {}): out["edits"].setdefault(src, {})[did] = disk["edits"][src][did]


def save(out, a, here):
    """Write --out through a temporary file and refresh the viewer's data files, so that reloading ocr_word_labels_viewer.html shows the results so far."""
    merge_from_disk(out, a.out)
    json.dump(out, open(a.out + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(a.out + ".tmp", a.out)
    if not a.no_viewer:
        try:
            sys.path.insert(0, here); from llm_to_viewer import export_to_viewer
            export_to_viewer(load_union(out, os.path.dirname(os.path.abspath(a.out))), a.model, os.path.join(here, "viewer_data"))   # the viewer shows all languages, whichever run saved last
        except Exception as err: print("viewer data not updated:", err, file=sys.stderr)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(here, "..", "data")); ap.add_argument("--base", default="v1.0", help="data version to read")
    ap.add_argument("--version", default="v1.1-llm", help="version name stored in the corrections file")
    ap.add_argument("--out", help="corrections file (default: corrections/v1.1-llm_ref-corrections_<lang>.json when one language is chosen with --lang, e.g. _en; otherwise corrections/v1.1-llm_ref-corrections.json). One file per language, so runs of two languages never write to the same file")
    ap.add_argument("--model", default="gpt-6-luna"); ap.add_argument("--effort", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--only", nargs="*", help="collections to do, e.g. icdar2017/en impresso-snippets/fr (default: all train files)")
    ap.add_argument("--split", nargs="*", default=["train"], choices=["train", "dev", "test"], help="splits to do (default: train); e.g. --split dev test. The edits are proposals for the annotators to review in the viewer; results on dev and test are always scored on the official references")
    ap.add_argument("--lang", nargs="*", help="languages to do, e.g. fr, or en fr (default: all); combine with --only to pick one collection")
    ap.add_argument("--max-units", type=int, help="stop after this many units (for a test)"); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--revalidate", action="store_true", help="no API call: check the edits already in --out (applied and rejected) again against the current rules, e.g. after the rules changed")
    ap.add_argument("--no-viewer", action="store_true", help="do not update the viewer's data files (viewer_data/llm_review.js and llm_corrected.js) at every save")
    ap.add_argument("--hyphens", action="store_true", help="second pass for units that were already done: ask again, with the hyphen rule, only for units whose (current) reference has a hyphen inside a word, and add the result to the earlier edits")
    ap.add_argument("--quiet", action="store_true", help="do not print every applied edit above the progress bar")
    ap.add_argument("--run", action="store_true", help="really call the API (without it: dry run)")
    a = ap.parse_args()

    if not a.out: a.out = os.path.join(here, "..", "corrections", "v1.1-llm_ref-corrections" + ("_" + a.lang[0] if a.lang and len(a.lang) == 1 else "") + ("" if a.split == ["train"] else "_" + "-".join(a.split)) + ".json")
    root = os.path.join(a.data, a.base)
    files = sorted(f for f in glob.glob(os.path.join(root, "*", "*", "*.jsonl")) if any(f"_{s}_" in os.path.basename(f) for s in a.split) and "unmatched" not in f and "masked" not in f)
    if a.only: files = [f for f in files if any(os.path.relpath(f, root).startswith(o.rstrip("/") + "/") for o in a.only)]
    if a.lang: files = [f for f in files if os.path.relpath(f, root).split(os.sep)[1] in a.lang]
    out = json.load(open(a.out, encoding="utf-8")) if os.path.exists(a.out) else {"version": a.version, "base": a.base, "edits": {}, "corrected": {}, "discarded": {}, "llm_log": {}}
    if a.revalidate:
        refs = {}
        for f in files:
            src = os.path.relpath(f, root)
            for line in open(f, encoding="utf-8"):
                r = json.loads(line); refs[(src, r["document_metadata"]["document_id"])] = r["ground_truth"]["transcription_unit"]
        gained = lost = 0
        for src, units in out["llm_log"].items():
            for did, log in units.items():
                if (src, did) not in refs: continue
                ref = refs[(src, did)]; cand = [{"find": e["find"], "replace": e["replace"], "reason": e.get("reason", ""), "confidence": e.get("confidence")} for e in log["applied"] + log["rejected"]]
                ok, bad = validate(cand, ref, "icdar" in src.split("/")[0]); new, used, skipped = apply_edits(ref, ok)
                gained += max(0, len(used) - len(log["applied"])); lost += max(0, len(log["applied"]) - len(used))
                out["llm_log"][src][did] = {"applied": used, "rejected": bad + skipped}
                if new != ref: out["edits"].setdefault(src, {})[did] = new
                else: out["edits"].get(src, {}).pop(did, None)
        save(out, a, here)
        print("revalidated %d units: %d edits newly accepted, %d no longer accepted -> %s" % (sum(len(v) for v in out["llm_log"].values()), gained, lost, a.out)); return
    JOURNAL = a.out.replace(".json", ".journal.jsonl")
    nj = load_journal(out, JOURNAL)
    if nj: print("journal: %d finished units read from %s" % (nj, JOURNAL))
    elsewhere = load_union({"llm_log": {}}, os.path.dirname(os.path.abspath(a.out)))["llm_log"]   # units done in the other files of the folder (another language, or the old single file)
    jobs = []
    for f in files:
        src = os.path.relpath(f, root)
        for line in open(f, encoding="utf-8"):
            r = json.loads(line); did = r["document_metadata"]["document_id"]
            if r["document_metadata"].get("discarded"): continue
            orig = r["ground_truth"]["transcription_unit"]; logged = out["llm_log"].get(src, {}).get(did) or (None if a.hyphens else elsewhere.get(src, {}).get(did))
            if a.hyphens:   # second pass: only units already done, not yet asked about hyphens, with a hyphen between letters in the current text
                cur = out["edits"].get(src, {}).get(did, orig)
                if logged is None or logged.get("hyphen_pass") or not WORD_HYPHEN.search(cur): continue
                jobs.append((src, did, cur, (r.get("ocr_hypothesis") or {}).get("transcription_unit", ""), "icdar" in src.split("/")[0], orig, True)); continue
            if logged is not None: continue
            jobs.append((src, did, orig, (r.get("ocr_hypothesis") or {}).get("transcription_unit", ""), "icdar" in src.split("/")[0], orig, False))
    if a.max_units: jobs = jobs[: a.max_units]
    chars = sum(len(j[2]) + len(j[3]) for j in jobs)
    print("%d files, %d units to do (%d already in %s), about %d characters (~%d tokens) of input in total" % (len(files), len(jobs), sum(len(v) for v in out["llm_log"].values()), a.out, chars, chars // 3))
    for s in sorted({j[0] for j in jobs}): print("  ", s, sum(1 for j in jobs if j[0] == s))
    if not a.run: print("dry run: nothing was sent. Add --run to call %s (effort %s)." % (a.model, a.effort)); return
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY is not set")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out["model"] = a.model   # shown in the viewer
    save(out, a, here)   # at once: the units already done (from an earlier run) show in the viewer before the first new unit is finished
    lock, done, n_edit, tok, n_fail = threading.Lock(), [0], [0], [0], [0]
    bar = tqdm(total=len(jobs), unit="unit", desc=a.model, dynamic_ncols=True)

    def work(j):
        src, did, ref, ocr, icdar, orig, hp = j
        edits, usage = ask(a.model, a.effort, key, ref, ocr, icdar)
        ok, bad = validate(edits, ref, icdar); new, used, skipped = apply_edits(ref, ok)
        with lock:
            if hp:   # second pass: add to the first pass (the text `ref` already holds its edits)
                old = out["llm_log"][src][did]; out["llm_log"][src][did] = {"applied": old["applied"] + used, "rejected": old["rejected"] + bad + skipped, "hyphen_pass": True}
                if new != ref: out["edits"].setdefault(src, {})[did] = new; n_edit[0] += 1
            else:
                out["llm_log"].setdefault(src, {})[did] = {"applied": used, "rejected": bad + skipped}
                if new != ref: out["edits"].setdefault(src, {})[did] = new; n_edit[0] += 1
            journal_append(JOURNAL, out, src, did)   # first of all: this unit is now safe
            done[0] += 1; tok[0] += usage.get("total_tokens", 0)
            if not a.quiet:
                for e in used: bar.write("%s %s  %r -> %r  (%s) %s" % (src.split("/")[0] + "/" + src.split("/")[1], did[-18:], e["find"][:40], e["replace"][:40], e["confidence"], e["reason"][:70]))
                for e in bad + skipped: bar.write("  rejected: %r -> %r  (%s)" % (e["find"][:40], e["replace"][:40], e["rejected"]))
            bar.update(1); bar.set_postfix(edited=n_edit[0], failed=n_fail[0], tokens=tok[0])
            if done[0] % 10 == 0 or done[0] == len(jobs):   # save every 10 units, through a temporary file
                save(out, a, here)

    with cf.ThreadPoolExecutor(a.workers) as ex:
        for fut in cf.as_completed([ex.submit(work, j) for j in jobs]):
            try: fut.result()
            except Exception as err:
                with lock: n_fail[0] += 1; bar.set_postfix(edited=n_edit[0], failed=n_fail[0], tokens=tok[0])
                bar.write("unit failed (it stays undone and is retried on the next run): %s" % err)
    bar.close()
    save(out, a, here)
    print("done: %d units, %d with edits -> %s" % (done[0], n_edit[0], a.out))


if __name__ == "__main__":
    main()
