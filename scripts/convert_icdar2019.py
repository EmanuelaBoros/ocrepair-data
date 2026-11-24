#!/usr/bin/env python3
"""Convert the ICDAR 2019 post-OCR competition data (Zenodo 3515403, ICDAR2019-POCR-ground-truth.zip) to the
benchmark jsonl format, one folder per sub-collection, and set the German material aside as it is.

usage: convert_icdar2019.py ICDAR2019-POCR-ground-truth.zip DATA_DIR [KEEP_LANGS]      (KEEP_LANGS default: en,fr)

  DATA_DIR/v1.0/icdar2019/<lang>/hipe-ocrepair-bench_v1.0_icdar2019_v1.0_<split>_<lang>.jsonl   (not German, except DE4-DE7; the
                                  sub-collections of a language, e.g. FR1+FR2+FR3, are in one file, told apart by document_id)
  DATA_DIR/v0.95/de-to-check/<training_18M|evaluation_4M>/DE/DE1..DE7/*.txt            (German, untouched)

Each .txt of the competition holds one text chunk as [OCR_toInput], [OCR_aligned] and [ GS_aligned]. The OCR text is
OCR_toInput, the reference is GS_aligned without the "@" gap marks and without "#" (no gold standard there).
The competition's own 80/20 split is kept: training -> train, evaluation -> test. Finnish is not in the archive.
"""
import json, os, re, sys, zipfile
from rapidfuzz.distance import Levenshtein

zip_path, out = sys.argv[1], sys.argv[2]
KEEP = set((sys.argv[3] if len(sys.argv) > 3 else "en,fr").split(","))
LANG = {"BG": "bg", "CZ": "cs", "EN": "en", "ES": "es", "FR": "fr", "NL": "nl", "PL": "pl", "SL": "sk"}   # SL = Slovak National Library
# German sub-collections that are converted here (DE1 = NZZ and DE3 = dta19 are already in the benchmark, DE2 is CC BY-NC-ND: left as they are)
CONVERT_DE = {"DE4": "la", "DE5": "la", "DE6": "de", "DE7": "de"}      # DE4 and DE5 are Latin, DE6 early new high German, DE7 German Fraktur
LICENSE = {"DE4": "CC BY-SA 4.0", "DE5": "CC BY-SA 4.0", "DE6": "CC BY-SA 4.0", "DE7": "CC BY-SA 4.0", "BG1": "CC BY-NC-ND", "CZ1": "CC BY-NC-SA", "EN1": "CC BY-NC-SA 3.0", "ES1": "CC BY-NC-SA", "FR1": "CC0",
           "FR2": "CC BY-NC-SA 3.0", "FR3": "CC0", "NL1": "CC BY", "PL1": "CC BY", "SL1": "CC BY-NC"}
SOURCE = {"DE4": "GT4Hist - EarlyModernLatin", "DE5": "GT4Hist - Kallimachos", "DE6": "GT4Hist - RefCorpus-ENHG-Incunabula",
          "DE7": "GT4Hist - RIDGES-Fraktur", "BG1": "IMPACT - National Library of Bulgaria", "CZ1": "IMPACT - National Library of the Czech Republic",
          "EN1": "IMPACT - British Library", "ES1": "IMPACT - National Library of Spain", "FR1": "HIMANIS project",
          "FR2": "IMPACT - National Library of France", "FR3": "RECEIPT dataset", "NL1": "IMPACT - National library of the Netherlands",
          "PL1": "IMPACT - National Library of Poland", "SL1": "IMPACT - Slovak National Library"}
SPLIT = {"training_18M_without_Finnish": "train", "evaluation_4M_without_Finnish": "test"}
PLACEHOLDER = {"transcription_unit": "None", "ocr_postcorrection_system": "None", "num_tokens": -1, "num_chars": -1,
               "quality_report": {"ocr_quality_score": -1, "cer": -1, "wer": -1, "nb_char_substitutions": -1,
                                  "nb_char_deletions": -1, "nb_char_insertions": -1}}
TAGS = ("[OCR_toInput] ", "[OCR_aligned] ", "[ GS_aligned] ")

z = zipfile.ZipFile(zip_path)
names = [n for n in z.namelist() if n.endswith(".txt")]
assert not any(n.startswith("/") or ".." in n.split("/") for n in names)

# German: copy as it is
de = 0
for n in names:
    top, rest = n.split("/", 1)
    if top in SPLIT and rest.startswith("DE/") and rest.split("/")[1] not in CONVERT_DE:
        dst = os.path.join(out, "v0.95/de-to-check", "training_18M" if SPLIT[top] == "train" else "evaluation_4M", rest)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(z.read(n)); de += 1
print("German files set aside:", de)

rows, stats = {}, {}
for n in sorted(names, key=lambda s: (s.split("/")[0], s.split("/")[2], int(re.sub(r"\D", "", os.path.basename(s)) or 0))):
    top, lg, sc, fn = n.split("/")
    if top not in SPLIT or (lg == "DE" and sc not in CONVERT_DE): continue
    split, lang = SPLIT[top], CONVERT_DE.get(sc) or LANG[lg]
    lines = z.read(n).decode("utf-8").split("\n")
    assert [l.startswith(t) for l, t in zip(lines[:3], TAGS)] == [True] * 3, n
    ocr_in, ocr_al, gs_al = (l[len(t):] for l, t in zip(lines[:3], TAGS))
    gs = re.sub(r"\s+", " ", gs_al.replace("@", "").replace("#", "")).strip()
    ocr = re.sub(r"\s+", " ", ocr_in).strip()
    st = stats.setdefault((sc, split), {"units": 0, "gs_hash": 0, "aligned_ok": 0, "chars": 0})
    st["units"] += 1; st["gs_hash"] += gs_al.count("#"); st["chars"] += len(gs)
    st["aligned_ok"] += re.sub(r"\s+", " ", ocr_al.replace("@", "")).strip() == ocr
    ops = Levenshtein.editops(ocr, gs)
    sub = sum(o.tag == "replace" for o in ops); ins = sum(o.tag == "delete" for o in ops); dele = sum(o.tag == "insert" for o in ops)  # relative to the OCR text
    cer = Levenshtein.distance(ocr, gs) / max(len(gs), 1)
    wer = Levenshtein.distance(ocr.split(), gs.split()) / max(len(gs.split()), 1)
    ds = "icdar2019-" + sc.lower(); num = os.path.splitext(fn)[0]
    rows.setdefault((lang, split), []).append({
        "document_metadata": {"document_id": f"icdar2019_{sc.lower()}_{split}_{lang}_{num}", "primary_dataset_name": "icdar2019",
            "primary_dataset_filename": n, "primary_dataset_version": "v1", "primary_dataset_license": f"{LICENSE[sc]} ({SOURCE[sc]})",
            "primary_dataset_url": "https://zenodo.org/record/3515403", "benchmark_dataset_name": "hipe-ocrepair-bench-icdar2019",
            "benchmark_dataset_doi": "n/a", "benchmark_dataset_split": split, "document_type": "receipt" if sc == "FR3" else "n/a",
            "date": "n/a", "language": lang, "publication_title": f"icdar 2019 - {lang} - {sc} - file {num}", "transcription_unit_scope": "chunk",
            "segmentation_origin_article": "primary-dataset - legacy", "segmentation_origin_sentences": "n/a", "segmentation_origin_paragraphs": "n/a"},
        "ground_truth": {"transcription_unit": gs, "line_offsets": [], "sentence_offsets": [], "num_tokens": len(gs.split()), "num_chars": len(gs),
                         "quality_report": {"ocr_quality_score": 1.0}},
        "ocr_hypothesis": {"transcription_unit": ocr, "line_offsets": [], "sentence_offsets": [], "num_tokens": len(ocr.split()), "num_chars": len(ocr),
                           "quality_report": {"ocr_quality_score": round(max(0.0, 1 - cer), 2), "cer": round(cer, 5), "wer": round(wer, 6),
                                              "nb_char_substitutions": sub, "nb_char_deletions": dele, "nb_char_insertions": ins}},
        "ocr_postcorrection_output": PLACEHOLDER})

for (lang, split), rs in sorted(rows.items()):
    d = os.path.join(out, "v1.0" if lang in KEEP else "v0.95/other-languages", "icdar2019", lang); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"hipe-ocrepair-bench_v1.0_icdar2019_v1.0_{split}_{lang}.jsonl"), "w", encoding="utf-8") as f:
        for r in rs: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"icdar2019 {lang} {split:5} {len(rs):5} units")
print("\nper sub-collection and split: units, units whose OCR_aligned matches OCR_toInput, '#' (no gold) characters, gold characters")
for (sc, split), s in sorted(stats.items()): print(f"  {sc} {split:5} {s['units']:5}  {s['aligned_ok']:5}  {s['gs_hash']:6}  {s['chars']:8}")
