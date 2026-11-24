#!/usr/bin/env python3
"""dta19 references write capital I as J (Jch, Jn, Jtalien, ...). Change that J to I, in place, for one version folder.

usage: fix_dta_J.py data/v0.10

Rules, reference text only:
  * J at the start of a word, followed by a consonant (Jch, Jhr, Jnhalt, JV)        -> I
  * words made only of Roman-numeral letters that contain J, length >= 2 (JJJ, XJ)  -> J becomes I
Words with J before a vowel (Jahr, Jugend, Jetzt, Jesus) and a lone "J" are left alone.
Offsets do not change (one character for one character). The OCR text is not touched.
"""
import glob, json, os, re, sys

CONS = "BCDFGHKLMNPQRSTVWXZbcdfghklmnpqrstvwxzſß"
WORDSTART_J = re.compile(r"(?<![^\W\d_])J(?=[" + CONS + "])")
ROMAN = re.compile(r"(?<![^\W\d_])[IVXLCDMJ]{2,}(?![^\W\d_])")


def fix(t):
    t = WORDSTART_J.sub("I", t)
    return ROMAN.sub(lambda m: m.group().replace("J", "I"), t)


root = sys.argv[1]
files = units = chars = 0
for f in sorted(glob.glob(os.path.join(root, "dta19", "*", "*.jsonl"))):
    if "masked" in f: continue
    raw = open(f, encoding="utf-8").read().split("\n")
    trailing = raw[-1] == ""
    out, ch = [], 0
    for line in (raw[:-1] if trailing else raw):
        r = json.loads(line)
        t = r["ground_truth"]["transcription_unit"]
        t2 = fix(t)
        if t2 != t:
            assert len(t2) == len(t)
            r["ground_truth"]["transcription_unit"] = t2
            out.append(json.dumps(r, ensure_ascii=False)); ch += 1
            chars += sum(a != b for a, b in zip(t, t2))
        else:
            out.append(line)
    if ch:
        open(f, "w", encoding="utf-8").write("\n".join(out) + ("\n" if trailing else ""))
        files += 1; units += ch
        print(f"{os.path.basename(f)[19:]:62} units changed: {ch}")
print(f"{files} files, {units} units, {chars} characters J -> I")
