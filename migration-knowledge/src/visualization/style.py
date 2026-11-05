"""Shared figure style (validated palette; see research/methodology.md §Figures).

Palette roles were checked with the dataviz validator (scripts/validate_palette.js):
the three layer colours (blue, orange, aqua) pass all adjacent-pair CVD and
normal-vision checks on the light surface; aqua is below 3:1 contrast, so every
layer colour is always accompanied by a direct text label (panel titles /
legends), never colour alone. Diverging encodings use blue <-> red with a grey
midpoint. Grey is used only for de-emphasized context marks.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
LAYER = {"migration": "#2a78d6", "scholars": "#eb6834", "collaboration": "#1baf7a"}
STRONGER = "#2a78d6"
WEAKER = "#e34948"
CONTEXT = "#c3c2b7"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = LinearSegmentedColormap.from_list(
    "blue_grey_red", ["#184f95", "#3987e5", "#9ec5f4", "#f0efec", "#f3a3a2", "#e34948", "#a62c2b"])

SOURCE_NOTE = ("Sources: UN DESA International Migrant Stock 2024; Akbaritabar, Theile & Zagheni (2024) "
               "scholarly migration data (OpenAlex-derived); OpenAlex; CEPII GeoDist; World Bank WDI.")


def apply() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 9.5, "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.labelsize": 9.5,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "svg.fonttype": "none", "pdf.fonttype": 42,
    })


def headline(fig, title: str, subtitle: str | None = None) -> None:
    fig.text(0.01, 0.985, title, ha="left", va="top", fontsize=13, fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.01, 0.945, subtitle, ha="left", va="top", fontsize=9.5, color=INK2, wrap=True)


def footnote(fig, text: str) -> None:
    fig.text(0.01, 0.01, text, ha="left", va="bottom", fontsize=7.2, color=MUTED, wrap=True)


def save(fig, out_dir: Path, stem: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / f"{stem}.svg", out_dir / f"{stem}.png"]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], dpi=300, bbox_inches="tight")
    plt.close(fig)
    return paths
