"""
spectra.py  -  neat-juice spectra for the juice spectrophotometer
-----------------------------------------------------------------
Separate from pipeline.py, which does concentration calibration.
This script answers a different question: what does each juice look
like across the AS7343's channels, and can the four be told apart?

Usage
-----
    python analysis/spectra.py data/raw/<file>.csv
    python analysis/spectra.py data/raw/<file>.csv apple orange blackcurrant

With no labels given, every label in the file is plotted except the
housekeeping ones (dark, blank, swap) and the dilution points (c12.5,
c25, c50 ...), which belong to pipeline.py.

The CSV must contain:
  - one or more rows labelled 'dark'   (LED off)
  - one or more rows labelled 'blank'  (water, LED on)

Licence: MIT
"""

import sys
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Channel table.  Peak wavelengths from the AS7343 datasheet.
# VIS is a clear (unfiltered) channel, so it has no wavelength and is
# used only as an intensity check, never plotted on the spectrum.
# ---------------------------------------------------------------------
CHANNELS = [
    ("F1",  405), ("F2",  425), ("FZ",  450), ("F3",  475),
    ("F4",  515), ("F5",  550), ("FY",  555), ("FXL", 600),
    ("F6",  640), ("F7",  690), ("F8",  745), ("NIR", 855),
]
CH = [c for c, _ in CHANNELS]
WL = [w for _, w in CHANNELS]

MIN_BLANK = 500      # a channel needs this many blank counts to be trusted
FIG_DIR = Path("analysis/figures")

# Labels that are not juices
HOUSEKEEPING = {"dark", "blank", "blank_close", "swap", "darklidoff", "darklidon"}
IS_DILUTION = re.compile(r"^c\d+(\.\d+)?$")

# Colours chosen to suggest each juice; override freely.
COLOURS = {
    "pineapple":    "#D4860B",
    "apple":        "#5B9E3F",
    "orange":       "#D4442B",
    "blackcurrant": "#7B3F9E",
}
FALLBACK = ["#2C6EBB", "#C0392B", "#2E7D52", "#8A5A9E", "#B58900", "#1F2328"]


def load(path):
    """Read the logger CSV and check it has what we need."""
    df = pd.read_csv(path)
    if "label" not in df.columns:
        raise ValueError("No 'label' column. Is this a logger.py file?")
    missing = [c for c in CH if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing channel columns: {missing}\n"
            "If the headers read col0, col1 ... the logger discarded the "
            "sketch's header line. Fix logger.py and re-log, or repair the "
            "header by hand."
        )
    for need in ("dark", "blank"):
        if (df.label == need).sum() == 0:
            raise ValueError(
                f"No rows labelled '{need}'. Found labels: "
                f"{sorted(df.label.unique())}"
            )
    return df


def juice_labels(df, asked):
    """Which labels to plot."""
    if asked:
        unknown = [a for a in asked if a not in set(df.label)]
        if unknown:
            raise ValueError(f"Not in the file: {unknown}")
        return asked
    out = []
    for lab in df.label.unique():
        if lab in HOUSEKEEPING or IS_DILUTION.match(str(lab)):
            continue
        out.append(lab)
    return out


def absorbance(df, label, dark, blank_net):
    """
    Mean absorbance for one label, with a per-replicate spread.

    Returns (A_mean, A_sd, n, floored) where `floored` marks channels
    whose counts have fallen to the stray-light / dark floor.  For those
    channels the absorbance is a LOWER BOUND, not a measurement.
    """
    rows = df[df.label == label][CH].astype(float)
    net = rows.values - dark.values                     # per-replicate net counts
    floor = np.maximum(20.0, 0.01 * blank_net.values)   # same rule as pipeline.py
    floored = (net.mean(axis=0) < floor)
    A = -np.log10(np.clip(net, 1e-9, None) / blank_net.values)
    return A.mean(axis=0), (A.std(axis=0, ddof=1) if len(A) > 1 else np.zeros(len(CH))), len(A), floored


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    asked = sys.argv[2:]

    df = load(path)
    dark = df[df.label == "dark"][CH].astype(float).mean()
    blank_net = df[df.label == "blank"][CH].astype(float).mean() - dark

    usable = [c for c in CH if blank_net[c] >= MIN_BLANK]
    if not usable:
        sys.exit(f"No channel reached {MIN_BLANK} blank counts. Raise the gain.")
    idx = [CH.index(c) for c in usable]
    wl_u = [WL[i] for i in idx]

    print(f"\nFile    : {path.name}")
    print(f"Blank   : {int(blank_net.max())} counts max "
          f"({blank_net.idxmax()}), {len(usable)}/{len(CH)} channels usable")
    print(f"Excluded: {[c for c in CH if c not in usable]}  (< {MIN_BLANK} counts)\n")

    labels = juice_labels(df, asked)
    if not labels:
        sys.exit("No juice labels found. Pass them explicitly, e.g.:\n"
                 "  python analysis/spectra.py <file>.csv apple orange")

    # ---------------- compute ----------------
    results = {}
    for lab in labels:
        A, sd, n, floored = absorbance(df, lab, dark, blank_net)
        results[lab] = dict(A=A, sd=sd, n=n, floored=floored)

    # ---------------- table ----------------
    head = f"{'label':14s}{'n':>3s}" + "".join(f"{c:>8s}" for c in usable)
    print(head)
    print("-" * len(head))
    for lab in labels:
        r = results[lab]
        line = f"{lab[:14]:14s}{r['n']:3d}"
        for c in usable:
            i = CH.index(c)
            v = r["A"][i]
            line += f"{'  >' + format(v, '.1f') if r['floored'][i] else format(v, '8.3f'):>8s}"
        print(line)
    print("\n'>' marks a channel at the measurement floor: the juice is too "
          "dark or too turbid to measure at this path length, so the value is "
          "a lower bound. Dilute and re-run.\n")

    for lab in labels:
        f = results[lab]["floored"][idx]
        if f.all():
            print(f"  WARNING: {lab} is over-range on EVERY usable channel. "
                  "Its spectrum carries no shape information — dilute it.")
        elif f.any():
            bad = [c for c, flag in zip(usable, f) if flag]
            print(f"  note: {lab} over-range on {', '.join(bad)}")

    # ---------------- plot ----------------
    ink = "#1f2328"
    plt.rcParams.update({
        "font.size": 9, "axes.edgecolor": ink, "axes.labelcolor": ink,
        "text.color": ink, "xtick.color": ink, "ytick.color": ink,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })
    fig, ax = plt.subplots(1, 2, figsize=(10.4, 4.0))

    def colour(lab, k):
        for key, col in COLOURS.items():
            if key in lab.lower():
                return col
        return FALLBACK[k % len(FALLBACK)]

    # (a) absolute absorbance
    a = ax[0]
    ymax = 0.0
    for k, lab in enumerate(labels):
        r = results[lab]
        col = colour(lab, k)
        if r["floored"][idx].all():
            continue                       # drawn as a capped marker below
        y = r["A"][idx]
        e = r["sd"][idx]
        a.errorbar(wl_u, y, yerr=e if r["n"] > 1 else None, fmt="o-", color=col,
                   mec="white", ms=6, lw=1.8, capsize=3, label=f"{lab} (n={r['n']})")
        ymax = max(ymax, float(np.nanmax(y + e)))

    cap = ymax * 1.12 if ymax > 0 else 1.0
    for k, lab in enumerate(labels):
        r = results[lab]
        if not r["floored"][idx].all():
            continue
        col = colour(lab, k)
        a.plot(wl_u, [cap] * len(wl_u), lw=0, marker="^", ms=7, mfc=col, mec=col)
        a.text(np.mean(wl_u), cap * 1.03, f"{lab}: beyond dynamic range",
               color=col, fontsize=8, ha="center")

    a.set_xlabel("Channel peak wavelength (nm)")
    a.set_ylabel("Absorbance (AU)")
    a.set_title("(a) Neat juice spectra", loc="left", fontweight="bold", fontsize=10)
    a.legend(frameon=False, fontsize=8)
    a.set_ylim(-0.05 * cap, cap * 1.15)

    # (b) normalised shape
    b = ax[1]
    for k, lab in enumerate(labels):
        r = results[lab]
        if r["floored"][idx].all():
            continue
        y = r["A"][idx]
        tot = y.sum()
        if tot <= 0:
            continue
        b.plot(wl_u, y / tot, "o-", color=colour(lab, k), mec="white",
               ms=6, lw=1.8, label=lab)
    b.set_xlabel("Channel peak wavelength (nm)")
    b.set_ylabel("Fraction of total absorbance")
    b.set_title("(b) Normalised shape — what a classifier sees",
                loc="left", fontweight="bold", fontsize=10)
    b.legend(frameon=False, fontsize=8)

    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / f"{path.stem}_spectra.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
