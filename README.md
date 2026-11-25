# OCR Post-Correction Data: HIPE-OCRepair-2026 data and its revised versions

This repository takes the data of the [HIPE-OCRepair-2026](https://hipe-eval.github.io/HIPE-OCRepair-2026/) competition and records the modifications made to it in new versions. It is **not** a competition repository: there is no task, submission or leaderboard here. The competition data is kept unchanged in `data/v0.9/`; corrections, additions (such as the data of the ICDAR 2019 post-OCR competition) and the choice of what to keep go into the later versions `data/v0.95/` and `data/v1.0/`. See [Versions in this repository](#versions-in-this-repository).

## About the original competition

[HIPE-OCRepair-2026](https://hipe-eval.github.io/HIPE-OCRepair-2026/) was an [ICDAR 2026 Competition](https://icdar2026.org/index.php/competitions/) focused on **LLM-assisted OCR post-correction of historical documents**, with a particular emphasis on historical newspapers.

With renewed interest driven by large language models (LLMs), OCR post-correction has (re)gained momentum, resulting in a growing number of models and experimental approaches. However, these efforts often rely on heterogeneous legacy datasets that come with important limitations, making systematic evaluation and meaningful comparison across approaches difficult.

A central question motivating the competition was:

> **To what extent can modern large language models address the OCR debt accumulated in large-scale digitized historical collections?**

The competition addressed this by providing **HIPE-OCRepair-Bench**, a unified multilingual benchmark for OCR post-correction, comprising curated datasets, an evaluation protocol, baseline systems, and an open leaderboard.

## 📋 Participation Guidelines (original competition)

All information about the task, datasets, evaluation protocol, and submission instructions is available in the **[Participation Guidelines](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/blob/main/README-Participation-Guidelines.md)**.

## 🔗 Important Links (original competition)

|                                              |                                                                                                        |
|----------------------------------------------|--------------------------------------------------------------------------------------------------------|
| 🌐 Competition website                       | https://hipe-eval.github.io/HIPE-OCRepair-2026/                                                        |
| 📋 Participation Guidelines                  | [README-Participation-Guidelines.md](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/blob/main/README-Participation-Guidelines.md)                               |
| 📈 Scorer                                    | [https://github.com/hipe-eval/HIPE-OCRepair-scorer](https://github.com/hipe-eval/HIPE-OCRepair-scorer) |
| 📊 Evaluation repository (after competition) | https://github.com/hipe-eval/HIPE-OCRepair-2026-eval                                                   |
| 🏆 Leaderboard (to come)                     | https://huggingface.co/spaces/hipe-ocrepair-2026-eval                                                  |
| 📝 Registration & contact                    | see competition website                                                                                |

## 📦 Data

Data is available:
- in the [data/](data/) folder of this repository and in the git [releases](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/releases)
- later: also on Zenodo

### Release History

- **20.04.2026**: Final competition release with **unmasked test files** with post-submission ground truth corrections | **Release tag** [v0.9.5](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/releases/tag/v0.9.5)
- **06.04.2026**: Release of **masked test files** for the competition | **Release tag** [v0.9.3](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/releases/tag/v0.9.3)
- **20.03.2026**: Release of train and dev sets for `dta19` dataset | **Release tag** [v0.9.2](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/releases/tag/v0.9.2)
- **11.03.2026**: Hot fix for `impresso-snippets` dataset | **Release tag** [v0.9.1](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/releases/tag/v0.9.1)
- **02.03.2026**: First data release with `overproof`, `icdar17`, `impresso-nzz` and `impresso-snippets` | **Release tag** [v0.9](https://github.com/hipe-eval/HIPE-OCRepair-2026-data/releases/tag/v0.9)

### Versions in this repository

The release history above describes the **official HIPE-OCRepair-2026 competition data**. This repository also contains additional, unofficial work on top of it, organised in `data/` by version:

| Folder | Content |
|--------|---------|
| `data/v0.9/` | The official competition data as released (`dta19`, `icdar2017`, `impresso-nzz`, `impresso-snippets`, `overproof`, all languages). **Unchanged.** |
| `data/v0.95/` | Data held back for now, to be checked later: `de-to-check/` (the German datasets `dta19`, `impresso-nzz` and `impresso-snippets/de`, with reference corrections, plus the ICDAR 2019 German sub-collections that overlap with them) and `other-languages/` (the other ICDAR 2019 languages, see below). |
| `data/v1.0/` | Current working version, **English and French only**: `icdar2017`, `impresso-snippets`, `overproof` and the added `icdar2019`. In the references of `impresso-snippets` and `overproof` the hyphenation mark `¬` is written as `-`. |

#### ICDAR 2019 post-OCR data

After the competition data, we added the data of the [ICDAR 2019 Competition on Post-OCR Text Correction](https://zenodo.org/record/3515403) (Rigaud, Doucet, Coustaty and Moreux, 2019), converted to the same `jsonl` format, keeping the competition's own train/test split. Its sub-collections come from different sources with different licenses (from CC0 to CC BY-NC-ND). `data/v1.0/icdar2019/` has the English and French parts; see [`data/v1.0/icdar2019/README.md`](data/v1.0/icdar2019/README.md) for sources and licenses, and [`scripts/convert_icdar2019.py`](scripts/convert_icdar2019.py) for the conversion. The other languages are in `data/v0.95/other-languages/icdar2019/`.

These additional versions are not official competition releases and have no release tags.

## 🙏 Sources and credits

The data in `data/v0.9/` is the data of the [HIPE-OCRepair-2026](https://hipe-eval.github.io/HIPE-OCRepair-2026/) competition (see its website for the organisers and the competition report), which in turn is built from the datasets below. The later versions are modifications of it and, for ICDAR 2019, an addition. Please credit the original sources when you use this data; the modifications in `v0.95` and `v1.0` are not made or endorsed by the original authors.

| Dataset | Original source | License (as recorded in the data files) |
|---------|-----------------|-----------------------------------------|
| `dta19` | [Deutsches Textarchiv](https://www.deutschestextarchiv.de/), GT4Hist ground truth ([10.5281/zenodo.1344132](https://doi.org/10.5281/zenodo.1344132)) | CC BY-SA 4.0 |
| `icdar2017` | [ICDAR 2017 Competition on Post-OCR Text Correction](https://sites.google.com/view/icdar2017-postcorrectionocr) | CC BY-NC-SA 4.0 |
| `impresso-nzz` | [NZZ black-letter ground truth](https://github.com/impresso/NZZ-black-letter-ground-truth/releases/tag/v1.1) ([10.5281/zenodo.3333627](https://doi.org/10.5281/zenodo.3333627)) | CC BY 4.0 |
| `impresso-snippets` | impresso project | CC BY-NC-SA 4.0 |
| `overproof` | [Overproof evaluation data](https://overproof.projectcomputing.com/evaluation) | "Very likely public domain, but not explicitly stated in original source." |
| `icdar2019` | [ICDAR 2019 Competition on Post-OCR Text Correction](https://zenodo.org/record/3515403), Rigaud, Doucet, Coustaty and Moreux | one license per sub-collection, see [`data/v1.0/icdar2019/README.md`](data/v1.0/icdar2019/README.md) |

The competition datasets are also described on Zenodo: [dta19](https://doi.org/10.5281/zenodo.18824344), [icdar2017](https://doi.org/10.5281/zenodo.18824428) and [overproof](https://doi.org/10.5281/zenodo.18824299).

## Annotating the reference transcriptions (viewer)

`viewers/ocr_word_labels_viewer.html` lets you check and correct the reference transcriptions of the splits in this repository. It is a static page; nothing is uploaded anywhere.

```bash
git clone https://github.com/EmanuelaBoros/ocrepair-data.git
cd ocrepair-data/viewers
python3 -m http.server 8000      # then open http://localhost:8000/ocr_word_labels_viewer.html
```

- The OCR is coloured by word class (unchanged, edited, retokenised, inserted); the reference can be edited in place. Words that may be wrong in the reference are listed on the right, with suggestions.
- Mark a unit "fully corrected" when you have checked it. Your edits and marks are kept in your browser (local storage).
- "Save corrections" downloads one JSON file (`hipe-ocrepair-bench_<version>_ref-corrections.json`) with your edited references and the units you marked corrected. Send it to us or open a pull request with it, so that annotators' files can be merged.
- Optional LLM-assisted proposals call the OpenAI API from your browser with your own key (kept for the browser session only).
- `viewers/build_viewer.py` rebuilds the page and `viewers/viewer_data/` from `viewers/viewer_template.html` and the data in `data/`.
