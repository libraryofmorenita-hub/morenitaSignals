"""
morenita_style.py — chart styling for Morenita Signals
Soft black & white, one gold accent (logo gold).

Themes:
  'ink'   — soft-black ground, gold accent (LinkedIn / cyber-deck)
  'paper' — soft-white ground, gold accent (print / light contexts)

Usage:
    from morenita_style import use_morenita, title, sign
    p = use_morenita("ink")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ...plot...  # first series = gold, rest = grayscale
    title(ax, "Headline", "subtitle", "ink")
    sign(fig, "Morenita Signals · 3,137 records", "ink")
    fig.savefig("chart.png", dpi=200, bbox_inches="tight")
"""

import matplotlib as mpl
from matplotlib import font_manager

GOLD = "#C9A24B"   # logo gold — the only color in the system

PALETTES = {
    "ink": {
        "bg":     "#161616",   # soft black
        "ink":    "#F2F0EB",   # soft white
        "muted":  "#9A968E",
        "grid":   "#2C2C2C",
        "gold":   GOLD,
        # gold leads; everything after is grayscale
        "series": [GOLD, "#F2F0EB", "#9A968E", "#5C5A55", "#3A3936"],
    },
    "paper": {
        "bg":     "#FAF3E3",   # warm cream (VS Code editor background)
        "ink":    "#3B2A1A",   # dark warm brown
        "muted":  "#8A7A56",   # muted olive-brown
        "grid":   "#EDE0C8",
        "gold":   GOLD,
        "series": [GOLD, "#3B2A1A", "#8A7A56", "#B5A788", "#DCD0B4"],
    },
}

def _font(names, fallback):
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for n in names:
        if n in installed:
            return n
    return fallback

DISPLAY = _font(["Cormorant Garamond", "Cormorant"], "serif")
BODY    = _font(["Inter", "Inter Display"], "sans-serif")

def use_morenita(theme="ink"):
    p = PALETTES[theme]
    mpl.rcParams.update({
        "figure.facecolor": p["bg"],
        "axes.facecolor":   p["bg"],
        "savefig.facecolor": p["bg"],
        "text.color":       p["ink"],
        "axes.edgecolor":   p["grid"],
        "axes.labelcolor":  p["muted"],
        "xtick.color":      p["muted"],
        "ytick.color":      p["muted"],
        "grid.color":       p["grid"],
        "grid.linewidth":   0.7,
        "axes.grid":        True,
        "axes.grid.axis":   "y",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.spines.left":   False,
        "axes.prop_cycle":  mpl.cycler(color=p["series"]),
        "font.family":      BODY,
        "font.size":        11,
        "axes.labelsize":   10,
        "xtick.labelsize":  9.5,
        "ytick.labelsize":  9.5,
        "legend.frameon":   False,
        "figure.dpi":       110,
    })
    return p

def title(ax, text, sub=None, theme="ink"):
    p = PALETTES[theme]
    ax.set_title(text, fontfamily=DISPLAY, fontsize=21,
                 color=p["ink"], loc="left", pad=26 if sub else 16)
    if sub:
        ax.text(0, 1.045, sub, transform=ax.transAxes,
                fontsize=9.5, color=p["muted"], fontfamily=BODY)

def sign(fig, text, theme="ink"):
    p = PALETTES[theme]
    fig.text(0.01, 0.005, text, fontsize=8, color=p["muted"],
             fontfamily=BODY, ha="left", va="bottom")

def highlight(ax, bars, index, theme="ink"):
    """Grayscale every bar except one — gold marks the point of the chart."""
    p = PALETTES[theme]
    grays = ["#5C5A55", "#7A7770", "#9A968E"] if theme == "ink" else ["#C9C6BE", "#AEABA3", "#8A877F"]
    for i, b in enumerate(bars):
        b.set_color(p["gold"] if i == index else grays[i % len(grays)])