# ICDAR 2019 post-OCR competition data: other languages (held back for now)

Source: Rigaud, Doucet, Coustaty, Moreux. *ICDAR 2019 Competition on Post-OCR Text Correction*,
https://zenodo.org/record/3515403 (`ICDAR2019-POCR-ground-truth.zip`). Converted with `scripts/convert_icdar2019.py`.
One file per language and split. The competition split is kept: training -> `train`, evaluation -> `test`.
One source file = one unit (about 3,000 characters, receipts shorter). Reference = `[ GS_aligned]` without the "@" gap marks and without
"#" (no gold standard there); OCR = `[OCR_toInput]`. `sentence_offsets` and `line_offsets` are empty; the OCR quality score is `1 - CER`.
The sub-collection of a unit is in its `document_id` (`icdar2019_<sub-collection>_<split>_<lang>_<n>`), `primary_dataset_filename`
and `primary_dataset_license`. Language codes are ISO 639-1. Finnish is not in the archive (the National Library of Finland does not allow re-sharing).

| language | sub-collection | source | license (Zenodo description) |
|---|---|---|---|
| bg | BG1 | IMPACT, National Library of Bulgaria | CC BY-NC-ND (**no derivatives: check before publishing**) |
| cs | CZ1 | IMPACT, National Library of the Czech Republic | CC BY-NC-SA |
| de | DE6 | GT4Hist RefCorpus-ENHG-Incunabula: early new high German incunabula (Cologne dialect) | CC BY-SA 4.0 |
| de | DE7 | GT4Hist RIDGES-Fraktur: German Fraktur herbals | CC BY-SA 4.0 |
| es | ES1 | IMPACT, National Library of Spain | CC BY-NC-SA |
| la | DE4 | GT4Hist EarlyModernLatin: Latin prints (listed under DE in the archive) | CC BY-SA 4.0 |
| la | DE5 | GT4Hist Kallimachos: Latin prints (listed under DE in the archive) | CC BY-SA 4.0 |
| nl | NL1 | IMPACT, National library of the Netherlands | CC BY |
| pl | PL1 | IMPACT, National Library of Poland | CC BY |
| sk | SL1 | IMPACT, Slovak National Library | CC BY-NC |

To bring a language back: `mv data/v0.95/other-languages/icdar2019/<lang> data/v1.0/icdar2019/`.
