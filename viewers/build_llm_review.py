#!/usr/bin/env python3
"""Resolve llm_review.json (text to find, replacement, reason) to unit ids in the version's data and write
viewer_data/llm_review.js for the viewer. dta19-l0 entries also apply to l1 and l2 (same reference text).

usage: build_llm_review.py [--data DIR] [--version v1.0]
"""
import argparse, glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("--data", default=os.path.join(HERE, "..", "data")); ap.add_argument("--version", default="v1.0")
a = ap.parse_args()
NAME = re.compile(r"^hipe-ocrepair-bench_v[\d.]+_(.+?)_v[\d.]+_(train|dev|test)_([a-z]{2})\.jsonl$")
units = {}
for f in glob.glob(os.path.join(a.data, a.version, "*/*/*.jsonl")):
    m = NAME.match(os.path.basename(f))
    if not m: continue
    ds, split, lang = m.groups()
    units[f"{ds}-{lang}|{split}"] = [(json.loads(l)["document_metadata"]["document_id"], json.loads(l)["ground_truth"]["transcription_unit"]) for l in open(f, encoding="utf-8")]
out, bad = [], 0
for e in json.load(open(os.path.join(HERE, "llm_review.json"), encoding="utf-8")):
    keys = [e["key"]] + ([e["key"].replace("-l0-", "-l1-"), e["key"].replace("-l0-", "-l2-")] if "dta19-l0" in e["key"] else [])
    for k in keys:
        hits = [(i, t.count(e["find"])) for i, t in units.get(k, []) if e["find"] in t]
        if len(hits) != 1 or hits[0][1] != 1:
            print("NOT UNIQUE / NOT FOUND:", k, repr(e["find"]), hits); bad += 1; continue
        out.append({"k": k, "id": hits[0][0], "find": e["find"], "rep": e["rep"], "conf": e["conf"], "why": e["why"]})
open(os.path.join(HERE, "viewer_data", "llm_review.js"), "w", encoding="utf-8").write("window.LLM=" + json.dumps(out, ensure_ascii=False) + ";\n")
print(len(out), "entries written;", bad, "problems")
