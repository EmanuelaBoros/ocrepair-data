#!/usr/bin/env python3
"""Rule-based correction of the train references, as a THIRD version on top of the LLM one (no LLM, no API call, free to run again and again).

A word list with frequencies decides what is a word: `pip install wordfreq` (French and English lists; zipf frequency, 0 = unknown, 3 = ordinary word, 6 = very common).
  A = first part, B = second part, AB = the joined word; "real" = zipf >= 3, "known" = zipf >= 2.
Rule 1, the mark "¬" followed by a space, left over from a word split at the end of a line ("Poi¬ tiers" -> "Poitiers", "plu¬ seurs" -> "plusieurs"):
  the mark and the space are removed, unless A and B are both real words and AB is rarer than both (best¬ selected stays).
Rule 3 (Overproof only; the layout is not kept): a hyphen at the end of a line, with the word going on in the next line ("Mary-\nborough"), is joined when the joined form is a known word (or both parts are unknown), and the line break is removed in every case ("Maryborough", "Eng-\nland" gives "England", "Argyle-\nstreet" gives "Argyle-street").
Rule 2, a hyphen left over from hyphenation inside one word ("licen-cié" -> "licencié", "destina-tions" -> "destinations"): A-B is joined when
    - AB is known and at least one part is not a real word (licen-cié, carac-térisée), or
    - both parts are real words but AB is more frequent than both (com-me -> comme), or
    - AB is unknown but both parts are unknown (tenan-cière): a word split in two fragments;
  and it is left alone when both parts are real words and AB is not more frequent (to-day, half-past, pare-chocs), when AB is unknown and a part is a real word
  (Belle-villoise, sous-marins), and for names (two capitalised parts: Saint-Denis, Jacquelin-Rettich).
The rules run on the LLM version of each unit when llm_correct_refs.py has done it (--llm), otherwise on the original reference.

usage:  python3 viewers/rule_correct_refs.py [--llm corrections/v1.1-llm_ref-corrections.json] [--lang fr] [--only icdar2017] [--show 30]
writes: corrections/v1.1-llm-rules_ref-corrections.json   (the edited references = LLM + rules, in the format of apply_ref_corrections.py, plus a "rules_log")
        viewers/viewer_data/rules_corrected.js             (what the viewer shows as the third version; reload the page)
"""
import argparse, glob, json, os, re, sys
try:
    from wordfreq import zipf_frequency
except ImportError:
    sys.exit("the word list is missing: pip install wordfreq")

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = re.compile(r"^hipe-ocrepair-bench_v[\d.]+_(.+?)_v[\d.]+_(train|dev|test)_([a-z]{2})\.jsonl$")
WORD = re.compile(r"(?<![\w-])[^\W\d_]+(?![\w-])")                   # a word without hyphen
NOT = re.compile(r"(?<![^\W\d_])([^\W\d_]{2,})¬\s*([^\W\d_]{2,})(?![^\W\d_])")   # A¬ B : "¬" is the mark of a word split at the end of a line (Poi¬ tiers)
NLHYPH = re.compile(r"(?<![\w-])([^\W\d_]{2,})-\n([^\W\d_]{2,})(?![\w-])")   # a hyphen at the end of a line and the word goes on in the next line (Overproof): the layout is not kept
HYPH = re.compile(r"(?<![\w-])([^\W\d_]{2,})-([^\W\d_]{2,})(?![\w-])")  # exactly one hyphen between two letter strings


KNOWN, REAL = 2.0, 3.0   # zipf frequency: a known word, an ordinary word


def z(word, lang):
    return zipf_frequency(word.lower(), lang)


def join_hyphens(text, lang, newlines=False):
    """Returns the new text and the list of joins made. newlines=True (Overproof): a line-end hyphen followed by a line break is treated like the other hyphens (joined, or kept as a hyphen), and the line break is removed in both cases."""
    log = []

    def fix_not(m):
        a, b = m.group(1), m.group(2); za, zb, zj = z(a, lang), z(b, lang), z(a + b, lang)
        if za >= REAL and zb >= REAL and zj < max(za, zb): return m.group(0)   # two real words (best¬ selected)
        log.append({"find": m.group(0), "replace": a + b, "rule": "line-end mark ¬ inside a word", "zipf": [za, zb, zj]})
        return a + b

    def fix(m):
        a, b = m.group(1), m.group(2); za, zb, zj = z(a, lang), z(b, lang), z(a + b, lang)
        if a[0].isupper() and b[0].isupper() and not (a.isupper() and b.isupper()): return m.group(0)   # a name (Saint-Denis)
        if zj >= KNOWN: ok = (za < REAL or zb < REAL) or zj >= max(za, zb)
        else: ok = za < KNOWN and zb < KNOWN                      # an unknown word made of two unknown fragments
        if not ok: return m.group(0)
        log.append({"find": m.group(0), "replace": a + b, "rule": "line-end hyphen inside a word", "zipf": [za, zb, zj]})
        return a + b

    def fix_nl(m):
        a, b = m.group(1), m.group(2); za, zb, zj = z(a, lang), z(b, lang), z(a + b, lang)
        keep = not (zj >= KNOWN or (za < KNOWN and zb < KNOWN))   # at the end of a line the hyphen is almost always hyphenation: join unless the joined form is not a word (Argyle-street)
        new = a + "-" + b if keep else a + b
        log.append({"find": m.group(0), "replace": new, "rule": "line-end hyphen and line break" + (" (real hyphen kept)" if keep else ""), "zipf": [za, zb, zj]})
        return new

    if newlines: text = NLHYPH.sub(fix_nl, text)
    return HYPH.sub(fix, NOT.sub(fix_not, text)), log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(HERE, "..", "data")); ap.add_argument("--base", default="v1.0")
    ap.add_argument("--llm", default=os.path.join(HERE, "..", "corrections", "v1.1-llm_ref-corrections.json"), help="corrections file of llm_correct_refs.py (optional); the files with the same start (..._en.json, ..._fr.json) are read too")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "corrections", "v1.1-llm-rules_ref-corrections.json"))
    ap.add_argument("--viewer-data", default=os.path.join(HERE, "viewer_data"))
    ap.add_argument("--only", nargs="*"); ap.add_argument("--lang", nargs="*"); ap.add_argument("--split", nargs="*", default=["train", "dev", "test"], choices=["train", "dev", "test"], help="splits to do (default: all three; the output file and the viewer data are rewritten for exactly these splits)"); ap.add_argument("--show", type=int, default=20, help="print this many examples")
    a = ap.parse_args()

    root = os.path.join(a.data, a.base)
    sys.path.insert(0, HERE); from llm_correct_refs import load_union
    llm = load_union({"llm_log": {}}, os.path.dirname(os.path.abspath(a.llm)), os.path.basename(a.llm).replace(".json", ""))   # all files of the folder: _en, _fr, the old single file
    files = sorted(f for f in glob.glob(os.path.join(root, "*", "*", "*.jsonl")) if any(f"_{s}_" in os.path.basename(f) for s in a.split) and "unmatched" not in f and "masked" not in f)
    if a.only: files = [f for f in files if any(os.path.relpath(f, root).startswith(o.rstrip("/")) for o in a.only)]
    if a.lang: files = [f for f in files if os.path.relpath(f, root).split(os.sep)[1] in a.lang]
    out = {"version": "v1.1-llm-rules", "base": a.base, "model": "rules on top of the LLM", "edits": {}, "corrected": {}, "discarded": {}, "rules_log": {}}
    texts, n_units, n_changed, n_joins, examples = {}, 0, 0, 0, []
    for f in files:
        src = os.path.relpath(f, root); m = NAME.match(os.path.basename(f)); lang = m.group(3)
        for line in open(f, encoding="utf-8"):
            r = json.loads(line); did = r["document_metadata"]["document_id"]
            if r["document_metadata"].get("discarded"): continue
            orig = r["ground_truth"]["transcription_unit"]; base = llm["edits"].get(src, {}).get(did, orig)   # the LLM version, or the original
            new, log = join_hyphens(base, lang, newlines=m.group(1).startswith("overproof")); n_units += 1
            key = f"{m.group(1)}-{lang}|{m.group(2)}\u0001{did}"
            texts[key] = new if new != base else ""       # "" = the rules changed nothing
            if new != orig: out["edits"].setdefault(src, {})[did] = new
            if log:
                out["rules_log"].setdefault(src, {})[did] = log; n_changed += 1; n_joins += len(log); examples += [(src.split("/")[0] + "/" + lang, e["find"], e["replace"], e["zipf"]) for e in log]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(a.out + ".tmp", a.out)
    open(os.path.join(a.viewer_data, "rules_corrected.js"), "w", encoding="utf-8").write("window.RULEST=" + json.dumps(texts, ensure_ascii=False) + ";\n")
    print("%d units, %d changed by the rules (%d hyphens joined); %d units hold an LLM edit the rules were applied on" % (n_units, n_changed, n_joins, sum(len(v) for v in llm["edits"].values())))
    print("written:", a.out, "and", os.path.join(a.viewer_data, "rules_corrected.js"))
    import random; random.seed(0)
    for c, f, r, fr in random.sample(examples, min(a.show, len(examples))): print("  %-14s %-22s -> %-20s (zipf of the two parts and of the joined word: %s)" % (c, f, r, fr))


if __name__ == "__main__":
    main()
