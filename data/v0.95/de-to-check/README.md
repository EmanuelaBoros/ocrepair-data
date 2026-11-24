# ICDAR 2019 post-OCR competition, German material (set aside, not converted)

Same source as `../../v1.0/icdar2019/README.md` (https://zenodo.org/record/3515403). DE4 to DE7 (GT4Hist, CC BY-SA 4.0) were converted and moved to `../other-languages/icdar2019/` (`de` and `la`).
Files as in the archive
(`[OCR_toInput]`, `[OCR_aligned]`, `[ GS_aligned]`), split into the competition's training and evaluation parts.

| folder | source | license (Zenodo description) |
|---|---|---|
| DE1 | Front pages of the Swiss newspaper NZZ (https://zenodo.org/record/3333627) | CC BY 4.0 (the benchmark already has `impresso-nzz`: check overlap) |
| DE2 | IMPACT, German National Library | CC BY-NC-ND (no derivatives) |
| DE3 | GT4Hist dta19 (https://zenodo.org/record/1344132) | CC BY-SA 4.0 (the benchmark already has `dta19`: check overlap) |

## Benchmark datasets moved here for now

`v1.0/` in this folder holds the German datasets taken out of `data/v1.0`: `dta19` (l0, l1, l2), `impresso-nzz` and
`impresso-snippets/de`, with the same sub-folders and file names as before. `data/v0.9` is unchanged and still has them.
`impresso-snippets` en and fr are still in `data/v1.0`.
To put them back: `git mv data/v0.95/de-to-check/v1.0/<dataset> data/v1.0/<dataset>`.
