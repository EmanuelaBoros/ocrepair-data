#!/usr/bin/env python3
"""Apply corrections saved from ocr_word_labels_viewer.html to the benchmark files.

usage: apply_ref_corrections.py hipe-ocrepair-bench_v1.1_ref-corrections.json [--data DIR] [--from v1.0] [--drop-discarded]

Reads data/<from>/<dataset>/<lang>/hipe-ocrepair-bench_<from>_*.jsonl and writes the
same files to data/<version>/... with <from> replaced by <version> in the folder and
file names. Only units that were edited or marked fully corrected are changed. Units discarded in the viewer (reference very different from
the OCR) get document_metadata.discarded = true, and are left out of the new files with --drop-discarded; their edits are ignored.
"""
import argparse, difflib, json, os, re, sys

p = argparse.ArgumentParser()
p.add_argument("corrections")
p.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
p.add_argument("--from", dest="old", default="v1.0")
p.add_argument("--drop-discarded", action="store_true")
a = p.parse_args()

C = json.load(open(a.corrections, encoding="utf-8"))
new = C["version"]
a.old = C.get("base", a.old)            # version the viewer was built from
if new == a.old:
    sys.exit("new version equals source version; refusing to overwrite the source files")


def remap(offsets, old, newt):
    """Move [start, end] character offsets from text `old` to text `newt`."""
    if not offsets:
        return offsets
    ops = difflib.SequenceMatcher(None, old, newt, autojunk=False).get_opcodes()

    def pos(x):
        for tag, i1, i2, j1, j2 in ops:
            if i1 <= x <= i2:
                return j1 + (x - i1 if tag == "equal" else (j2 - j1 if x == i2 else 0))
        return len(newt)

    return [[pos(s), pos(e)] for s, e in offsets]


n_edit = n_ok = 0
n_disc = 0
for src in sorted(set(C["edits"]) | set(C["corrected"]) | set(C.get("discarded", {}))):
    edits, ok, disc = C["edits"].get(src, {}), set(C["corrected"].get(src, [])), set(C.get("discarded", {}).get(src, []))
    inp = os.path.join(a.data, a.old, src)
    rel = re.sub(r"(hipe-ocrepair-bench_)" + re.escape(a.old) + "_", r"\g<1>" + new + "_", src, count=1)   # only the benchmark version, not a dataset version such as overproof-combined_v1.0
    out = os.path.join(a.data, new, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = []
    src_lines = open(inp, encoding="utf-8").read().splitlines()
    ids = [json.loads(l)["document_metadata"]["document_id"] for l in src_lines if l.strip()]
    dup = {i for i in ids if ids.count(i) > 1}   # two units with one document id: the edits are stored by id and would be applied to both, so these units are left as they are
    if dup: print("  skipped (document id shared by two units):", sorted(dup)[:3], "in", src)
    for line in src_lines:
        if not line.strip(): continue
        r = json.loads(line)
        did = r["document_metadata"]["document_id"]
        if did in dup: edits = {k: v for k, v in edits.items() if k != did}; ok = ok - {did}; disc = disc - {did}
        g = r["ground_truth"]
        if did in disc:
            n_disc += 1
            if a.drop_discarded:
                continue
            r["document_metadata"]["discarded"] = True
            lines.append(json.dumps(r, ensure_ascii=False))
            continue
        if did in edits and edits[did] != g["transcription_unit"]:
            old_t, new_t = g["transcription_unit"], edits[did]
            if g.get("num_tokens") == len(old_t.split()):
                g["num_tokens"] = len(new_t.split())
            g["num_chars"] = len(new_t)
            for k in ("line_offsets", "sentence_offsets", "paragraph_offsets"):
                if k in g:
                    g[k] = remap(g[k], old_t, new_t)
            g["transcription_unit"] = new_t
            n_edit += 1
        if did in ok:
            r["document_metadata"]["manually_corrected"] = True
            n_ok += 1
        lines.append(json.dumps(r, ensure_ascii=False))
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(out)
print(f"{n_edit} units edited, {n_ok} marked fully corrected, {n_disc} discarded" + (" (dropped)" if a.drop_discarded else " (flagged)"))
