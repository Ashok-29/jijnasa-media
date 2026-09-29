#!/usr/bin/env python3
"""Brand chart for a carousel 'chart' slide or an X image. Numbers must come from the claim map.

  python3 kit/chart.py chart.json out.png [--x]   # --x renders 1600x900 for X; default 912x620 for a slide

chart.json: {"kind": "bar"|"hbar"|"line", "title": "", "labels": [...], "values": [...],
             "unit": "km/s", "highlight": 2, "source": "Data: NASA (2026)", "note": ""}
"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAVY, GOLD, GOLD2, INK, MUTED = "#0b1428", "#e8b24a", "#f6d58c", "#f3ead7", "#b9b09c"


def draw(c, out, x=False):
    w, h, dpi = ((16, 9, 100) if x else (9.12, 6.2, 100))
    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi)
    fig.patch.set_facecolor(NAVY); ax.set_facecolor(NAVY)
    L, V = c["labels"], c["values"]; hi = c.get("highlight")
    cols = [GOLD if (hi is None or i == hi) else "#3a4a6b" for i in range(len(V))]
    fs = 22 if x else 17
    if c["kind"] == "line":
        ax.plot(L, V, color=GOLD, lw=4, marker="o", ms=9)
        for i, v in enumerate(V):
            if i in (0, len(V) - 1) or i == hi:
                ax.annotate(f"{v:,.10g}", (L[i], v), textcoords="offset points", xytext=(0, 12), ha="center", color=GOLD2, fontsize=fs, weight="bold")
    elif c["kind"] == "hbar":
        bars = ax.barh(L, V, color=cols); ax.invert_yaxis()
        for b, v in zip(bars, V):
            ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f"  {v:,.10g}", va="center", color=INK, fontsize=fs, weight="bold")
    else:
        bars = ax.bar(L, V, color=cols)
        for b, v in zip(bars, V):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v:,.10g}", ha="center", va="bottom", color=INK, fontsize=fs, weight="bold")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=fs - 3)
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    val_axis = ax.xaxis if c["kind"] == "hbar" else ax.yaxis
    val_axis.set_major_locator(MaxNLocator(4)); val_axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.10g}"))
    unit_axis = ax.xaxis if c["kind"] == "hbar" else ax.yaxis
    unit_axis.set_label_text(c.get("unit", ""), color=MUTED, fontsize=fs - 3)
    ax.grid(axis="x" if c["kind"] == "hbar" else "y", color="#2a3654", lw=1)
    ax.set_axisbelow(True)
    if x and c.get("title"):
        fig.suptitle(c["title"], color=INK, fontsize=34, weight="bold", x=0.06, ha="left", y=0.95)
    fig.text(0.06 if x else 0.02, 0.02, c.get("source", ""), color=MUTED, fontsize=fs - 5)
    if x: fig.text(0.94, 0.02, "Jijñāsā", color=GOLD, fontsize=fs, ha="right", weight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.9 if x else 1))
    fig.savefig(out, facecolor=NAVY); print("saved", out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(0)
    c = json.load(open(sys.argv[1]))
    assert c.get("source"), "chart needs a 'source' line"
    assert len(c["labels"]) == len(c["values"]), "labels/values length mismatch"
    draw(c, sys.argv[2], "--x" in sys.argv)
