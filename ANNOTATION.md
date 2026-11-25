# Annotating the reference transcriptions

We are correcting errors in the reference transcriptions of the splits in this repository, with the browser viewer `viewers/ocr_word_labels_viewer.html`.

## Who annotates what

Two annotators, split by language so that nobody works on the same units:

| Annotator | Collections (viewer names) | Units |
|---|---|---|
| Emanuela | `icdar2017-fr`, `icdar2019-fr`, `impresso-snippets-fr` | 3,500 (all splits) |
| Wenjun | `icdar2017-en`, `icdar2019-en`, `impresso-snippets-en`, `overproof-combined-en` | 1,308 (all splits) |

Do only your own collections. `icdar2019-fr` is 2,849 units, most of the French share; if it needs to be shared, agree on unit ranges by hand (for example "units 1-1400 are Emanuela's") before starting. Each annotator saves a corrections file per session and commits it to `corrections/` (section 5); because the collections are disjoint, the two annotators' files can be merged without conflicts.

## How to annotate

We check and correct the **reference** (ground-truth) transcription of each unit, using the OCR text next to it. Use the table above to see which collections are yours.

## 1. Start the viewer

```bash
git clone https://github.com/EmanuelaBoros/ocrepair-data.git
cd ocrepair-data/viewers
python3 -m http.server 8000
```

Open <http://localhost:8000/ocr_word_labels_viewer.html> in your browser. Use the same browser every time: your edits and marks are kept in its local storage, and clearing the browser data deletes them. Nothing is uploaded; the page has no server. If you pulled a new version of the repository, restart the server and reload the page.

## 2. What you see

- **Left:** the list of collections and splits (use only yours), then the units of the selected split. At the top, a progress bar per collection shows how many units you marked fully corrected; click it to jump there.
- **Centre:** the OCR text (coloured by word class: edited, retokenised, inserted, unchanged) and below it the reference text. "Dim unchanged words" makes the words that differ easier to see.
- **Right:** words of the reference that may be wrong (odd characters, one letter from a common word, seen once), often with a suggested fix. Click an entry to jump to the word in the reference, or a suggestion to apply it.

## 3. What to correct

Fix only clear, certain errors in the **reference** text: a typo, a swapped or missing letter, a missing space after punctuation. Be conservative; if you are not sure, leave it.

- Do not add or delete words.
- Do not modernise or normalise: keep historical spellings, archaic and dialect forms, long s, ligatures, diacritics, capitalisation, abbreviations and the punctuation habits of the period, even where they look wrong today.
- Do not add or change quotation marks.
- Do not change numbers, names or dates unless the OCR text clearly shows that the reference has a typo.
- Do not touch other line breaks or hyphenation (see the exception below).

**Exception, ICDAR collections (`icdar2017-*`, `icdar2019-*`):** in the reference, a line break sometimes falls in the middle of a word (for example `exam` + line break + `ple`). Remove the line break so that the word is whole (`example`). Delete only the line break (do not add a space or a hyphen); a line break between two words stays as it is. If the break splits a word together with a hyphen, do not decide it yourself: leave it and note the unit, so that we can agree on one rule.

## 4. How to work on a unit

1. Select a unit and read the OCR and the reference. Click in the reference box to edit it in place; the colours disappear for an edited unit, and the unit is marked as edited in the list.
2. When you have checked the whole unit, press **Mark unit fully corrected** (press it again to undo). Units you checked but did not need to change should be marked too, so that progress is counted.
3. "Revert" undoes your edit of the unit.
4. The optional LLM button proposes corrections with the OpenAI API, called from your browser with your own key (kept for the browser session only). You see each proposal and accept or discard it; the same rules apply.

## 5. Save and share your work

1. Set the **version** field at the top to `v1.1-<your name>` (for example `v1.1-emanuela`, `v1.1-wenjun`).
2. Press **Save corrections**. The browser downloads `hipe-ocrepair-bench_v1.1-<your name>_ref-corrections.json`, which holds your edited references and the list of units you marked fully corrected.
3. Do this at the end of every session (it contains all of your work so far, not only the last session) and commit the file to the `corrections/` folder of this repository, by pull request or directly if you have write access. A newer file replaces your older one.

Because the two annotators work on different collections, the files can be merged without conflicts: the merged result is the union of the `edits` and `corrected` entries of both files.
