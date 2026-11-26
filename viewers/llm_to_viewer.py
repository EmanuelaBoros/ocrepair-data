#!/usr/bin/env python3
"""Show the edits of llm_correct_refs.py in the viewer: adds them to viewer_data/llm_review.js, where the viewer reads LLM proposals from, so that each one
appears in the "Possibly wrong in reference" panel with its reason, its confidence and an `apply` button. It also writes viewer_data/llm_corrected.js, the full corrected text of each unit, for the
comparison boxes under the reference (original GT, your version above, LLM version with the changes marked). Nothing is applied automatically; the annotator decides.

usage: python3 viewers/llm_to_viewer.py corrections/v1.1-llm_ref-corrections.json [--model gpt-6-luna] [--viewer-data viewers/viewer_data]
Run it again after a new LLM run: the entries of the earlier run (marked "src": "gpt") are replaced. Then reload the viewer page (restart the local server if it caches).
Only the units of the version the viewer was built from (data/<base>) are matched; a proposal whose text is not found exactly once in the viewer's reference is skipped.
"""
import argparse, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = re.compile(r"^hipe-ocrepair-bench_v[\d.]+_(.+?)_v[\d.]+_(train|dev|test)_([a-z]{2})\.jsonl$")   # same key as build_llm_review.py: <dataset>-<lang>|<split>


def export_to_viewer(C, model="", viewer_data=os.path.join(HERE, "viewer_data")):
    """C = the corrections dict of llm_correct_refs.py. Writes viewer_data/llm_review.js and viewer_data/llm_corrected.js; returns the number of proposals."""
    path = os.path.join(viewer_data, "llm_review.js")
    old = json.loads(re.sub(r"^window\.LLM=|;\s*$", "", open(path, encoding="utf-8").read())) if os.path.exists(path) else []
    keep = [e for e in old if e.get("src") != "gpt"]
    new = []
    for src, units in C.get("llm_log", {}).items():
        m = NAME.match(os.path.basename(src))
        if not m: continue
        ds, split, lang = m.groups(); k = f"{ds}-{lang}|{split}"
        for did, log in units.items():
            for e in log.get("applied", []):
                new.append({"k": k, "id": did, "find": e["find"], "rep": e["replace"], "conf": e["confidence"],
                            "why": ((e["reason"] + " ") if e.get("reason") else "") + ("[" + model + "]" if model else "[LLM]"), "src": "gpt"})
    texts = {}   # the full corrected reference of every unit the script did (the viewer's comparison boxes); "" = no change proposed
    for src, units in C.get("llm_log", {}).items():
        m = NAME.match(os.path.basename(src))
        if m:
            for did in units: texts[f"{m.group(1)}-{m.group(3)}|{m.group(2)}\u0001{did}"] = C.get("edits", {}).get(src, {}).get(did, "")
    for name, text in (("llm_review.js", "window.LLM=" + json.dumps(keep + new, ensure_ascii=False) + ";\n"),
                       ("llm_corrected.js", "window.LLMT_MODEL=" + json.dumps(model or "LLM") + ";window.LLMT=" + json.dumps(texts, ensure_ascii=False) + ";\n")):
        open(os.path.join(viewer_data, name + ".tmp"), "w", encoding="utf-8").write(text); os.replace(os.path.join(viewer_data, name + ".tmp"), os.path.join(viewer_data, name))
    return len(new)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("corrections"); ap.add_argument("--model", default=""); ap.add_argument("--viewer-data", default=os.path.join(HERE, "viewer_data"))
    a = ap.parse_args()
    print(export_to_viewer(json.load(open(a.corrections, encoding="utf-8")), a.model, a.viewer_data), "proposals written to", a.viewer_data)
