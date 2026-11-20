"""Writing tables (Excel/CSV) and simple, consistent static charts."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from . import config  # noqa: E402

# Validated categorical palette (fixed order) + text/surface tokens.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
APPROACH_COLOURS = {"Quantitative": SERIES[0], "Qualitative": SERIES[1], "Mixed methods": SERIES[2]}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
})


def _ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_tables(name: str, tables: dict[str, pd.DataFrame], folder: Path = config.TABLES) -> Path:
    """One workbook per section, one tab per table, with readable formatting."""
    path = _ensure(folder) / f"{name}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for sheet, df in tables.items():
            df.to_excel(xw, sheet_name=sheet[:31], index=df.index.name is not None or isinstance(df.index, pd.MultiIndex))
            format_sheet(xw.sheets[sheet[:31]])
    return path


def format_sheet(ws, max_width: int = 60):
    header_fill = PatternFill("solid", fgColor="1C5CAB")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        longest = max((len(str(c.value)) if c.value is not None else 0) for c in col[:200])
        ws.column_dimensions[letter].width = min(max(10, longest + 2), max_width)
        for c in col[1:]:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"


def hbar(counts: pd.Series, title: str, fname: str, xlabel: str = "Number of papers",
         colour: str = SERIES[0], note: str | None = None) -> Path:
    """Horizontal bar chart, largest at top, value labels at bar ends."""
    counts = counts.sort_values()
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(counts) + 1.4))
    bars = ax.barh(counts.index.astype(str), counts.values, color=colour, height=0.7)
    ax.bar_label(bars, padding=3, color=INK_2, fontsize=9)
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.margins(x=0.08)
    if note:
        fig.text(0.01, 0.005, note, fontsize=8, color=INK_2, ha="left", va="bottom")
    return _save(fig, fname)


def stacked_bar(table: pd.DataFrame, title: str, fname: str, xlabel: str = "",
                ylabel: str = "Number of papers", colours: dict | None = None) -> Path:
    """Vertical stacked bars (rows = x categories, columns = series)."""
    fig, ax = plt.subplots(figsize=(max(6, 0.45 * len(table) + 2), 4.2))
    bottom = pd.Series(0, index=table.index, dtype=float)
    for i, col in enumerate(table.columns):
        colour = (colours or {}).get(col, SERIES[i % len(SERIES)])
        ax.bar(table.index.astype(str), table[col], bottom=bottom, label=col, color=colour,
               edgecolor=SURFACE, linewidth=1.5, width=0.75)
        bottom += table[col]
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.yaxis.get_major_locator().set_params(integer=True)
    if table.shape[1] > 1:
        ax.legend(frameon=False, ncol=min(4, table.shape[1]), loc="upper left")
    plt.setp(ax.get_xticklabels(), rotation=45 if len(table) > 8 else 0, ha="right" if len(table) > 8 else "center")
    return _save(fig, fname)


def presence_grid(matrix: pd.DataFrame, title: str, fname: str) -> Path:
    """Papers (rows) x items (columns) grid; filled square = present."""
    m = matrix.astype(bool)
    fig, ax = plt.subplots(figsize=(0.55 * m.shape[1] + 3.5, 0.28 * m.shape[0] + 1.8))
    for r, (_, row) in enumerate(m.iterrows()):
        for c, val in enumerate(row):
            ax.add_patch(plt.Rectangle((c + 0.08, r + 0.08), 0.84, 0.84,
                                       color=SERIES[0] if val else "#eeedea"))
    ax.set_xlim(0, m.shape[1]); ax.set_ylim(m.shape[0], 0)
    ax.set_xticks([i + 0.5 for i in range(m.shape[1])])
    ax.set_xticklabels(m.columns, rotation=45, ha="right")
    ax.set_yticks([i + 0.5 for i in range(m.shape[0])])
    ax.set_yticklabels(m.index, fontsize=8)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, loc="left")
    return _save(fig, fname)


def _save(fig, fname: str) -> Path:
    path = _ensure(config.FIGURES) / f"{fname}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def explode_count(series: pd.Series, splitter) -> pd.Series:
    """Count items in a column whose cells hold lists (via splitter)."""
    return series.map(splitter).explode().dropna().value_counts()


def hstacked(table: pd.DataFrame, title: str, fname: str, xlabel: str = "Count",
             grey: tuple = ("Not stated",)) -> Path:
    """Horizontal stacked bars (rows = categories on y, columns = series),
    legend underneath. Columns named in `grey` are drawn last in neutral grey."""
    cols = [c for c in table.columns if c not in grey] + [c for c in table.columns if c in grey]
    table = table[cols]
    fig, ax = plt.subplots(figsize=(9, 0.55 * len(table) + 2.6))
    left = pd.Series(0, index=table.index, dtype=float)
    labels = table.index.astype(str)
    for i, col in enumerate(cols):
        colour = "#b5b4ae" if col in grey else SERIES[i % len(SERIES)]
        ax.barh(labels, table[col], left=left, label=col, color=colour,
                edgecolor=SURFACE, linewidth=1.5, height=0.65)
        left += table[col]
    for y, total in enumerate(left):
        ax.text(total + max(left) * 0.01, y, f"{int(total)}", va="center", color=INK_2, fontsize=9)
    ax.invert_yaxis()
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.45, -0.18), fontsize=9)
    return _save(fig, fname)
