# ICDAR 2019 post-OCR competition data: English and French

Source: Rigaud, Doucet, Coustaty, Moreux. *ICDAR 2019 Competition on Post-OCR Text Correction*,
https://zenodo.org/record/3515403 (`ICDAR2019-POCR-ground-truth.zip`). Converted with `scripts/convert_icdar2019.py`.
One file per language and split. The competition split is kept: training -> `train`, evaluation -> `test`.
One source file = one unit (about 3,000 characters, receipts shorter). Reference = `[ GS_aligned]` without the "@" gap marks and without
"#" (no gold standard there); OCR = `[OCR_toInput]`. `sentence_offsets` and `line_offsets` are empty; the OCR quality score is `1 - CER`.
The sub-collection of a unit is in its `document_id` (`icdar2019_<sub-collection>_<split>_<lang>_<n>`), `primary_dataset_filename`
and `primary_dataset_license`. Language codes are ISO 639-1. Finnish is not in the archive (the National Library of Finland does not allow re-sharing).
For now `v1.0` only has English and French. The other languages are in `../../v0.95/other-languages/icdar2019/`, the German
material that is already in the benchmark or cannot be derived from is in `../../v0.95/de-to-check/`.

| language | sub-collection | source | license (Zenodo description) |
|---|---|---|---|
| en | EN1 | IMPACT, British Library | CC BY-NC-SA 3.0 |
| fr | FR1 | HIMANIS project: 14th-15th century French royal chancery registers (handwritten, transcribed by HTR) | CC0 |
| fr | FR2 | IMPACT, National Library of France: printed books (17th century sample) | CC BY-NC-SA 3.0 |
| fr | FR3 | RECEIPT dataset: shop receipts | CC0 |

Notes: the gold standard quality varies between sub-collections and contains some errors (Zenodo description). Some units have an
empty reference or OCR text, or an OCR error rate above 100% (misaligned); they are kept. Not yet checked: overlap with ICDAR 2017 (en, fr).
