#!/usr/bin/env python3
"""Build the word-label viewer from the benchmark files.

usage: build_viewer.py [--data DIR] [--version v0.9]

Also lists, per unit, reference words that may be wrong (see suspects()).
Writes ocr_word_labels_viewer.html (small) and viewer_data/<collection>_<split>.js (one per file, loaded on
click). Every train/dev/test file under data/<version>/ is included; masked-test and *-unmatched files are not.
Word labels follow slm-ocr-postcorrection/results/ocr_word_labels.py (unchanged / edited / retokenised /
inserted for OCR words; unchanged / edited / retokenised / deleted for reference words), with the interval
lookups done by bisection so that page-sized units stay fast.
"""
import argparse, bisect, collections, difflib, glob, json, multiprocessing, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
WORD = re.compile(r"\S+")
squash = lambda s: re.sub(r"\s+", "", s)
ABBR = {"unchanged": "u", "edited": "e", "retokenised": "r", "inserted": "i", "deleted": "d"}


def label_pair(ref, ocr):
    ops = difflib.SequenceMatcher(None, ref, ocr, autojunk=False).get_opcodes()
    eq = [(b1, b2, a1 - b1) for tag, a1, a2, b1, b2 in ops if tag == "equal"]
    eq_b = [x[0] for x in eq]
    eq_a = [(a1, a2, b1) for tag, a1, a2, b1, b2 in ops if tag == "equal"]
    eq_a1 = [x[0] for x in eq_a]
    edits = [(a1, a2, b1, b2) for tag, a1, a2, b1, b2 in ops if tag != "equal"]
    e_b1, e_b2 = [x[2] for x in edits], [x[3] for x in edits]
    e_a1, e_a2 = [x[0] for x in edits], [x[1] for x in edits]
    ws_only = lambda a1, a2, b1, b2: squash(ref[a1:a2]) == squash(ocr[b1:b2])
    ref_words = [(m.start(), m.end()) for m in WORD.finditer(ref)]
    ref_set = set(ref_words)
    out_o, out_r, ref_ocr = [], [], []
    o_a2 = [x[2] for x in ops]

    def ocr_for(s, e):                                  # OCR word(s) lying over the reference span [s, e)
        i = bisect.bisect_right(o_a2, s)
        if i >= len(ops): return ""
        tag, a1, _, b1, b2 = ops[i]
        sb = b1 + (s - a1) if tag == "equal" else b1
        j = bisect.bisect_left(o_a2, e)
        if j >= len(ops): j = len(ops) - 1
        tag, a1, _, b1, b2 = ops[j]
        eb = b1 + (e - a1) if tag == "equal" else b2
        while sb > 0 and not ocr[sb - 1].isspace(): sb -= 1
        while eb < len(ocr) and not ocr[eb].isspace(): eb += 1
        return ocr[sb:eb] if sb < eb else ""

    for m in WORD.finditer(ocr):
        s, e = m.start(), m.end()
        hit = edits[bisect.bisect_right(e_b2, s):bisect.bisect_left(e_b1, e)]
        if hit:
            if all(ws_only(*x) for x in hit): cls = "retokenised"
            elif any(x[0] == x[1] and x[2] <= s and x[3] >= e for x in hit): cls = "inserted"
            else: cls = "edited"
        else:
            i = bisect.bisect_right(eq_b, s) - 1
            shift = eq[i][2] if i >= 0 and eq[i][0] <= s and e <= eq[i][1] else None
            cls = "unchanged" if shift is not None and (s + shift, e + shift) in ref_set else "retokenised"
        out_o.append((s, e, cls))
    for s, e in ref_words:
        hit = edits[bisect.bisect_right(e_a2, s):bisect.bisect_left(e_a1, e)]
        if hit:
            if all(ws_only(*x) for x in hit): cls = "retokenised"
            elif any(x[3] == x[2] and x[0] <= s and x[1] >= e for x in hit): cls = "deleted"
            else: cls = "edited"
        else:
            cls = "unchanged"
            i = bisect.bisect_right(eq_a1, s) - 1
            if i >= 0 and eq_a[i][0] <= s and e <= eq_a[i][1]:
                a1, _, b1 = eq_a[i]; os_ = s - a1 + b1
                cls = "unchanged" if any(m.start() == os_ and m.end() == os_ + (e - s)
                                         for m in WORD.finditer(ocr, max(os_ - 1, 0), os_ + (e - s) + 1)) else "retokenised"
        out_r.append((s, e, cls))
        ref_ocr.append(ocr_for(s, e))
    return out_o, out_r, ref_ocr


NAME = re.compile(r"^hipe-ocrepair-bench_v[\d.]+_(.+?)_v[\d.]+_(train|dev|test)_([a-z]{2})\.jsonl$")
ORDER = {"train": 0, "dev": 1, "test": 2}

# ---- suspicious reference words -------------------------------------------------------------------------------
MARKS = "\u0300-\u036f"
EDGE = re.compile(r"^[^\w%s]+|[^\w%s]+$" % (MARKS, MARKS))
ODD = re.compile(r"[|~^@#*_<>{}\[\]\\\u00ac]|[a-z\u00e4\u00f6\u00fc\u00df][A-Z\u00c4\u00d6\u00dc][a-z\u00e4\u00f6\u00fc\u00df]|(\w)\1\1|[^\W\d_]\d|\d[^\W\d_]|[^\W\d_]\u2014[^\W\d_]|[^\W\d_]{2}[.,;:!?][^\W\d_]")
FREQ_MIN = 10
VOCAB, INDEX_ = {}, {}                                # per language: Counter of words, deletion index of frequent words
norm = lambda w: EDGE.sub("", w).lower()
dehyphen = lambda t: re.sub(r"-\n(?=\S)", "", t)       # rejoin words split over lines, for counting only


def deletes(w, d=1):
    out = {w[:i] + w[i + 1:] for i in range(len(w))}
    if d == 2: out |= {x for y in out for x in deletes(y)}
    return out


def lev(a, b, mx=2):
    if abs(len(a) - len(b)) > mx: return mx + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


ORDINAL = re.compile(r"\d+(st|nd|rd|th|s|d|er|e|\u00e8me|me)?", re.I)
inflection = lambda a, b: a.startswith(b) or b.startswith(a) or a[:-1] == b[:-1]
GLUE = re.compile(r"^(.*?[^\W\d_]{2}[.,;:!?])([^\W\d_].*)$")
STRAY = re.compile(r"[|~^@#*_<>{}\[\]\\\u00ac]")


def candidates(lang, w):
    """Frequent words within edit distance 2 of w: [(distance, -count, word)]."""
    idx, voc = INDEX_[lang], VOCAB[lang]
    found = set()
    for d in {w} | deletes(w, 2):
        found |= idx.get(d, set())
    res = []
    for v in found:
        k = lev(w, v)
        if 0 < k <= 2 and (k == 1 or len(w) >= 5): res.append((k, -voc[v], v))
    return sorted(res)


def style_like(tok_core, v):
    if len(tok_core) > 1 and tok_core.isupper(): return v.upper()
    return v[:1].upper() + v[1:] if tok_core[:1].isupper() else v


def suspects(lang, ref, rw, ref_ocr):
    """[[start, end, codes, [suggestions]]] for reference words that may be wrong."""
    out = []
    voc = VOCAB[lang]
    for (s, e, c), oc in zip(rw, ref_ocr):
        tok = ref[s:e]
        if tok.endswith("-") and ref[e:e + 1] == "\n": continue            # first half of a line-end hyphenation
        if ref[max(s - 2, 0):s] == "-\n": continue                          # second half
        w = norm(tok)
        if len(w) < 3 or not any(ch.isalpha() for ch in w): continue
        codes, sugg = [], []
        core = EDGE.sub("", tok)
        i0 = tok.find(core) if core else 0
        lead, trail = tok[:i0], tok[i0 + len(core):]
        wrap = lambda x: lead + x + trail
        n = voc.get(w, 0)
        if (ODD.search(tok) or "\u00ac" in tok) and not ORDINAL.fullmatch(w):
            codes.append("chars")
            g = GLUE.match(tok)
            if g: sugg.append(g.group(1) + " " + g.group(2))
            if STRAY.search(tok): sugg.append(STRAY.sub("", tok))
        if c != "u" and n <= 1:                       # reference word seen once, and the OCR reads it differently
            cand = candidates(lang, w)
            if any(k == 1 and not inflection(w, v) for k, _, v in cand) and n < FREQ_MIN: codes.append("near")
            codes.append("rare")
            oc_core = EDGE.sub("", oc)
            if oc_core and not any(ch.isspace() for ch in oc_core) and norm(oc_core) != w and voc.get(norm(oc_core), 0) >= 2:
                sugg.insert(0, wrap(oc_core))                 # what the OCR has at this spot
            sugg += [wrap(style_like(core, v)) for k, _, v in cand[:4]]
        seen, uniq = {tok}, []
        for x in sugg:
            if x not in seen: seen.add(x); uniq.append(x)
        if codes: out.append([s, e, ",".join(codes), uniq[:4]])
    return out


def build_one(job):
    f, root = job
    m = NAME.match(os.path.basename(f))
    ds, split, lang = m.groups()
    key, stem = f"{ds}-{lang}|{split}", f"{ds}-{lang}_{split}"
    units = []
    for line in open(f, encoding="utf-8"):
        r = json.loads(line)
        ref, ocr = r["ground_truth"]["transcription_unit"], r["ocr_hypothesis"]["transcription_unit"]
        wo, wr, ref_ocr = label_pair(ref, ocr)
        rw = [[s, e, ABBR[c]] for s, e, c in wr]
        units.append({"id": r["document_metadata"]["document_id"], "src": os.path.relpath(f, root), "ocr": ocr, "ref": ref,
                      "w": [[s, e, ABBR[c]] for s, e, c in wo], "rw": rw, "sus": suspects(lang, ref, rw, ref_ocr)})
    with open(os.path.join(HERE, "viewer_data", stem + ".js"), "w", encoding="utf-8") as o:
        o.write("(window.D=window.D||{})[%s]=%s;\n" % (json.dumps(key), json.dumps(units, ensure_ascii=False, separators=(",", ":"))))
    return {"k": key, "ds": f"{ds}-{lang}", "split": split, "f": stem, "n": len(units), "sus": sum(len(u["sus"]) for u in units)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(HERE, "..", "data"))
    ap.add_argument("--version", default="v0.10")
    a = ap.parse_args()
    root = os.path.join(a.data, a.version)
    os.makedirs(os.path.join(HERE, "viewer_data"), exist_ok=True)
    files = [f for f in sorted(glob.glob(root + "/*/*/*.jsonl")) if NAME.match(os.path.basename(f))]
    # vocabulary: reference words per language; dta19-l1/l2 repeat the l0 reference, so they are not counted again
    for f in files:
        ds, split, lang = NAME.match(os.path.basename(f)).groups()
        if ds in ("dta19-l1", "dta19-l2"): continue
        c = VOCAB.setdefault(lang, collections.Counter())
        for line in open(f, encoding="utf-8"):
            for tok in WORD.findall(dehyphen(json.loads(line)["ground_truth"]["transcription_unit"])):
                w = norm(tok)
                if w: c[w] += 1
    for lang, c in VOCAB.items():
        idx = INDEX_.setdefault(lang, {})
        for v, n in c.items():
            if n >= FREQ_MIN and len(v) >= 4:
                for d in {v} | deletes(v, 2): idx.setdefault(d, set()).add(v)
    ctx = multiprocessing.get_context("fork")
    index = []
    with ctx.Pool(min(8, os.cpu_count() or 1)) as pool:
        for r in pool.imap_unordered(build_one, [(f, root) for f in files]):
            index.append(r); print(r["k"], r["n"], "units,", r["sus"], "suspects", flush=True)
    index.sort(key=lambda x: (x["ds"], ORDER[x["split"]]))
    nxt = re.sub(r"(\d+)$", lambda m: str(int(m.group(1)) + 1), a.version)
    html = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
    html = html.replace("/*INDEX*/[]", json.dumps(index)).replace("/*BASE*/", json.dumps(a.version)).replace("/*NEXT*/", nxt)
    open(os.path.join(HERE, "ocr_word_labels_viewer.html"), "w", encoding="utf-8").write(html)


if __name__ == "__main__":
    main()
