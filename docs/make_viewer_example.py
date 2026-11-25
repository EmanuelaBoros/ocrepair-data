"""Draws docs/viewer_example.png: how a unit looks in viewers/ocr_word_labels_viewer.html (same colours as the viewer's CSS), for a real unit
(icdar2017_train_fr_84_398) read from docs/_example_unit.json. It is an illustration drawn with matplotlib, not a screenshot.  python docs/make_viewer_example.py"""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
D = Path(__file__).resolve().parent; u = json.load(open(D / "_example_unit.json", encoding="utf-8"))
COL = {"u": ("#ffffff", None), "e": ("#f5b7b1", None), "r": ("#aed6f1", None), "i": ("#f9e79f", "#d4ac0d"), "d": ("#fadbd8", "#c0392b")}
fig = plt.figure(figsize=(12, 4.5), dpi=150); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1200); ax.set_ylim(450, 0); ax.axis("off")
fig.patch.set_facecolor("#fafafa"); r = fig.canvas.get_renderer()
def box(x, y, w, h, fc="#fff", ec="#ddd", lw=1, r_=6, ls="-"): ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r_}", fc=fc, ec=ec, lw=lw, ls=ls))
def text(x, y, s, size=10, color="#111", weight="normal", ha="left", style="normal"): return ax.text(x, y, s, fontsize=size, color=color, weight=weight, ha=ha, va="center", style=style, family="DejaVu Sans")
def button(x, y, s, fc="#efefef", color="#111", w=None):
    t = text(x + 8, y + 12, s, 9, color); bb = t.get_window_extent(r); ww = w or bb.width * 1200 / (12 * 150) + 16; box(x, y, ww, 24, fc, "#999", 1, 4); t.set_zorder(5); return x + ww + 6
# header
box(0, 0, 1200, 74, "#fff", "#ddd", 1, 0)
x = 12
for s in ("←", "→"): x = button(x, 8, s)
text(x + 4, 20, "version", 9); box(x + 48, 8, 56, 24, "#fff", "#999", 1, 3); text(x + 54, 20, "v1.1-name", 8); x += 112
x = button(x, 8, "Save corrections"); x = button(x, 8, "Revert this unit"); x = button(x, 8, "✔ Mark unit fully corrected", "#16a34a", "#fff")
x = button(x, 8, "Discard unit: reference very different from the OCR"); x = button(x, 8, "Correct whole unit (LLM)...")
text(14, 50, "Legend:", 9)
lx = 62
for k, lab in (("e", "edited"), ("r", "retokenised (segmentation only)"), ("i", "inserted (OCR only)"), ("d", "missing from OCR (reference only)"), ("u", "unchanged")):
    t = text(lx + 5, 50, lab, 8.5); w = t.get_window_extent(r).width * 1200 / (12 * 150) + 10; fc, ec = COL[k]; box(lx, 40, w, 20, fc, ec or "#ccc", 1, 3, "--" if k == "d" else "-"); t.set_zorder(5); lx += w + 10
# list columns
box(0, 74, 150, 376, "#fff", "#ddd", 1, 0); text(10, 90, "COLLECTION / SPLIT", 7.5, "#666", "bold")
for i, (a, b, sel) in enumerate((("icdar2017-fr", "", False), ("train", "491 units", True), ("test", "", False))):
    if sel: box(2, 112 + i * 30 - 6, 146, 30, "#e4e4e4", "#e4e4e4", 0, 0)
    text(12, 118 + i * 30, a, 8.5, "#777" if not sel else "#111", "bold" if sel else "normal")
box(150, 74, 190, 376, "#fff", "#ddd", 1, 0); text(160, 90, "UNITS", 7.5, "#666", "bold")
nerr = sum(1 for x in u["w"] if x[2] != "u")
box(151, 104, 188, 38, "#e4e4e4", "#e4e4e4", 0, 0); text(160, 114, "2. " + u["id"], 8, "#111", "bold"); text(160, 130, f"{nerr} errors", 7.5, "#777")
# OCR / reference panels
def panel(y0, title, txt, spans, h, sus=None):
    box(352, y0, 590, h, "#fff", "#ddd", 1, 6); text(366, y0 + 16, title, 7.5, "#666", "bold")
    x, y = 366, y0 + 44; spans = list(spans); p = 0
    for s, e, c in spans:
        for piece in ([txt[p:s]] if txt[p:s].strip() == "" else [txt[p:s]]): pass
        p = e; w_ = txt[s:e]
        t = text(x, y, w_, 10); wpx = t.get_window_extent(r).width * 1200 / (12 * 150)
        if x + wpx > 930: t.remove(); x = 366; y += 28; t = text(x, y, w_, 10)
        fc, ec = COL[c]
        if c != "u": box(x - 2, y - 11, wpx + 4, 22, fc, ec or fc, 1, 3, "--" if c == "d" else "-")
        if sus and s in sus: ax.plot([x - 2, x + wpx + 2], [y + 12, y + 12], color="#d97706", lw=1.6, ls=(0, (1, 1.2)))
        t.set_zorder(5); x += wpx + 8
panel(86, "OCR (COLOURED BY CLASS)", u["ocr"], u["w"], 150)
panel(246, "REFERENCE (COLOURED BY HOW OCR DID) — CLICK TO EDIT", u["ref"], u["rw"], 150, {s for s, e, *_ in u["sus"]})
import collections; n = collections.Counter(x[2] for x in u["w"]); N = len(u["w"])
text(366, 416, f"{N} words: unchanged {n['u']}, edited {n['e']}, retokenised {n['r']}, inserted {n['i']}  |  error rate {100*(1-n['u']/N):.1f}%", 8.5, "#555")
# right panel
box(950, 74, 250, 376, "#fff", "#ddd", 1, 0); text(960, 90, "POSSIBLY WRONG IN REFERENCE (1)", 7.5, "#666", "bold")
text(960, 118, "ANNEE.N°", 9.5, "#111", "bold"); text(960, 136, "odd characters / glued words; seen once", 7.5, "#b45309")
button(960, 148, "use: ANNEE. N°", "#eef2ff", "#111")
# explanation markers
for (x1, y1, x2, y2, s) in ((650, 100, 700, 438, "1"),):
    pass
def num(x, y, s): ax.add_patch(plt.Circle((x, y), 11, fc="#2a78d6", ec="white", lw=1.5, zorder=9)); ax.text(x, y, s, color="white", fontsize=9, weight="bold", ha="center", va="center", zorder=10)
num(620, 420 + 0, "1") if False else None
for (x, y, s) in ((926, 20, "1"), (330, 50, "2"), (344, 112, "3"), (335, 96 + 0, "3")):
    pass
for (x, y, s) in ((1180, 20, "1"), (790, 50, "2"), (920, 100, "3"), (920, 260, "4"), (1186, 100, "5"), (322, 146, "6")): num(x, y, s)
fig.savefig(D / "viewer_example.png"); print("wrote", D / "viewer_example.png")
