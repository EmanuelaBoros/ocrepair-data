# Version v1.1: references revised by an LLM and rules (English and French)

The same units as `../v1.0/` (same ids, same OCR text, same file layout), with the **reference** (`ground_truth.transcription_unit`) revised in 3,105 of 4,808 units. The OCR text is never touched.
File names have `v1.1` in place of the benchmark version (`hipe-ocrepair-bench_v1.1_..._train_en.jsonl`).

## How the references were revised

Three steps, all in this repository, no human review yet (the annotators can review and edit in the viewer, see `../../ANNOTATION.md`):

1. **LLM** (`viewers/llm_correct_refs.py`, OpenAI `gpt-6-luna`, medium reasoning effort): for every unit it receives the guideline, the reference and the OCR text and returns edits `{find, replace, reason, confidence}`. An edit is applied only if the text to find occurs once, no word or quotation mark is added and no line break is touched; the rejected ones are logged.
2. **Rules** (`viewers/rule_correct_refs.py`, no model, `pip install wordfreq`): joins a word split by a hyphen or by the mark `¬` at the end of a line when the word list says the joined form is a word (`destina-tions` to `destinations`, `Poi¬ tiers` to `Poitiers`); real hyphens, compounds and names stay. For Overproof only, a hyphen at the end of a line followed by a line break is joined in the same way and the line break is removed (`Mary-⏎borough` to `Maryborough`), because the layout is not kept.
3. **Build** (`viewers/apply_ref_corrections.py`): `python3 viewers/apply_ref_corrections.py corrections/v1.1-llm-rules_ref-corrections.json` (with the version field set to `v1.1`) writes these files. Units whose document id is shared by two units (two in `overproof` train) are left as they are, because edits are stored by id.

The edits of every step are in `../../corrections/` (`v1.1-llm_ref-corrections_*.json` for the LLM, `v1.1-llm-rules_ref-corrections.json` for LLM plus rules, with the log of the rules).

## Use

- Use **v1.1 for training** the correctors.
- For **evaluation against the competition** use the official references of `../v1.0/` (or `../v0.9/`): scores on v1.1 are not comparable with the participants' scores.
- `icdar2019` is not part of the shared task; it is the English and French data of the ICDAR 2019 competition on post-OCR text correction (Rigaud et al., 2019), converted in this repository, with its own train/test split (no dev).

## Content

| collection | language | split | units | references changed |
|---|---|---|---|---|
| icdar2017 | en | dev | 188 | 148 (79%) |
| icdar2017 | en | test | 101 | 35 (35%) |
| icdar2017 | en | train | 455 | 345 (76%) |
| icdar2017 | fr | test | 100 | 61 (61%) |
| icdar2017 | fr | train | 391 | 375 (96%) |
| icdar2019 | en | test | 48 | 36 (75%) |
| icdar2019 | en | train | 148 | 114 (77%) |
| icdar2019 | fr | test | 592 | 320 (54%) |
| icdar2019 | fr | train | 2,257 | 1,240 (55%) |
| impresso-snippets | en | dev | 10 | 9 (90%) |
| impresso-snippets | en | test | 100 | 74 (74%) |
| impresso-snippets | en | train | 50 | 39 (78%) |
| impresso-snippets | fr | dev | 10 | 10 (100%) |
| impresso-snippets | fr | test | 100 | 82 (82%) |
| impresso-snippets | fr | train | 50 | 21 (42%) |
| overproof | en | dev | 30 | 30 (100%) |
| overproof | en | test | 32 | 32 (100%) |
| overproof | en | train | 146 | 134 (92%) |

Total: 4,808 units, 3,105 with a changed reference. The viewer (`../../viewers/ocr_word_labels_viewer.html`) shows for every unit the original reference, the LLM version and the LLM version with the rules.
