"""
pipeline.py: analysis pipeline for the juice spectrophotometer
================================================================
Turns raw AS7343 counts into absorbance, fits calibration lines,
estimates the limit of detection (LOD), and makes the figures.

How to run (from the repo's top folder):
    python analysis/pipeline.py                       # demo with SIMULATED data
    python analysis/pipeline.py data/raw/myfile.csv   # analyse a real logger file

Input CSV format (what logger.py writes): one row per reading, with
    - a 'label' column:  'dark', 'blank', or 'c<number>' (concentration in %, e.g. c0, c25, c100)
    - one column per AS7343 channel: F1, F2, FZ, F3, F4, F5, FY, FXL, F6, F7, F8, NIR
Other columns (pc_time, temp_C, ...) are kept but ignored.

Absorbance for each channel:  A = -log10( (I_sample - I_dark) / (I_blank - I_dark) )
Licence: MIT
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # save figures to files (works without a screen)
import matplotlib.pyplot as plt
from scipy import stats

# ---------------------------------------------------------------------------
# AS7343 channels: name -> peak wavelength (nm), from docs/as7343_channels.md
# ---------------------------------------------------------------------------
CHANNELS = {
    "F1": 405, "F2": 425, "FZ": 450, "F3": 475, "F4": 515, "F5": 550,
    "FY": 555, "FXL": 600, "F6": 640, "F7": 690, "F8": 745, "NIR": 855,
}
CH = list(CHANNELS)                       # channel names, in wavelength order
WL = np.array(list(CHANNELS.values()))    # wavelengths (nm)

FIG_DIR = Path(__file__).resolve().parent / "figures"


# ---------------------------------------------------------------------------
# 1. Loading data
# ---------------------------------------------------------------------------
def load_csv(path):
    """Read a logger CSV and keep only rows that have a label and all 12 channels."""
    df = pd.read_csv(path)
    missing = [c for c in ["label"] + CH if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    df["label"] = df["label"].astype(str).str.strip()
    return df.dropna(subset=CH)


def concentration_of(label):
    """'c25' -> 25.0 ; 'blank' -> 0.0 ; 'dark' or anything else -> None."""
    if label == "blank":
        return 0.0
    m = re.fullmatch(r"c(\d+(?:\.\d+)?)", label)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# 2. Counts -> absorbance
# ---------------------------------------------------------------------------
def absorbance(sample, blank, dark):
    """
    Absorbance per channel from mean counts (arrays of length 12).
    Transmittance is clipped to a tiny positive number so log10 never fails.
    """
    T = (np.asarray(sample) - dark) / (np.asarray(blank) - dark)
    return -np.log10(np.clip(T, 1e-6, None))


def summarise(df):
    """
    Average the repeats for each label and convert to absorbance.
    Returns:
      table : one row per sample label -> concentration, mean A and SD of A per channel
      sd_blank_A : SD of absorbance between individual blank readings (for the LOD)
    """
    dark = df.loc[df.label == "dark", CH].mean().values
    blanks = df.loc[df.label == "blank", CH].values
    if len(blanks) == 0 or np.isnan(dark).any():
        raise ValueError("Need at least one 'dark' row and one 'blank' row.")
    blank = blanks.mean(axis=0)

    # Spread of individual blank readings, expressed in absorbance units
    sd_blank_A = absorbance(blanks, blank, dark).std(axis=0, ddof=1) if len(blanks) > 1 \
        else np.full(len(CH), np.nan)

    rows = []
    for label, grp in df.groupby("label", sort=False):
        c = concentration_of(label)
        if c is None:                      # skip 'dark' and unknown labels
            continue
        A_each = absorbance(grp[CH].values, blank, dark)     # every repeat
        rows.append({"label": label, "conc": c, "n": len(grp),
                     **{f"A_{ch}": A_each[:, i].mean() for i, ch in enumerate(CH)},
                     **{f"sd_{ch}": (A_each[:, i].std(ddof=1) if len(grp) > 1 else np.nan)
                        for i, ch in enumerate(CH)}})
    table = pd.DataFrame(rows).sort_values("conc").reset_index(drop=True)
    return table, sd_blank_A


# ---------------------------------------------------------------------------
# 3. Calibration (Beer-Lambert: A = slope * c + intercept)
# ---------------------------------------------------------------------------
def blank_counts(df):
    """Mean blank counts per channel, dark-corrected: how much light each channel actually saw."""
    dark = df.loc[df.label == "dark", CH].mean().values
    blank = df.loc[df.label == "blank", CH].mean().values
    return blank - dark


def calibrate(table, sd_blank_A, max_A=None):
    """
    Straight-line fit of mean A against concentration for every channel.
    max_A: optionally ignore points above this absorbance (outside the linear range).
    Returns a DataFrame: slope, its standard error, intercept, R^2, LOD and LOQ (in % units).
    """
    out = []
    for i, ch in enumerate(CH):
        x, y = table["conc"].values, table[f"A_{ch}"].values
        keep = np.ones_like(x, bool) if max_A is None else (y <= max_A)
        if keep.sum() < 3:
            continue
        fit = stats.linregress(x[keep], y[keep])
        lod = 3 * sd_blank_A[i] / fit.slope if fit.slope > 0 else np.nan
        loq = 10 * sd_blank_A[i] / fit.slope if fit.slope > 0 else np.nan
        out.append({"channel": ch, "wavelength_nm": CHANNELS[ch],
                    "slope_per_pct": fit.slope, "slope_se": fit.stderr,
                    "intercept": fit.intercept, "R2": fit.rvalue**2,
                    "LOD_pct": lod, "LOQ_pct": loq, "n_points": int(keep.sum())})
    return pd.DataFrame(out)


def predict_concentration(A, cal_row):
    """Concentration (%) from a measured absorbance, using one channel's calibration."""
    return (A - cal_row["intercept"]) / cal_row["slope_per_pct"]


# ---------------------------------------------------------------------------
# 4. Figures
# ---------------------------------------------------------------------------
def plot_spectra(table, name):
    """Absorbance vs wavelength, one line per concentration."""
    fig, ax = plt.subplots(figsize=(6, 4))
    for _, r in table.iterrows():
        A = [r[f"A_{ch}"] for ch in CH]
        sd = [r[f"sd_{ch}"] for ch in CH]
        ax.errorbar(WL, A, yerr=sd, marker="o", ms=3, capsize=2, label=r["label"])
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absorbance")
    ax.set_title("Absorbance spectra")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    path = FIG_DIR / f"{name}_spectra.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_calibration(table, cal, ch, name):
    """Calibration line + residuals for one channel."""
    r = cal.set_index("channel").loc[ch]
    x, y, sd = table["conc"].values, table[f"A_{ch}"].values, table[f"sd_{ch}"].values
    fit_y = r["slope_per_pct"] * x + r["intercept"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.errorbar(x, y, yerr=sd, fmt="o", capsize=3, label="measured (mean ± SD)")
    xx = np.linspace(0, x.max(), 100)
    ax1.plot(xx, r["slope_per_pct"] * xx + r["intercept"], "-",
             label=f"fit: R² = {r['R2']:.4f}")
    ax1.set_ylabel(f"Absorbance ({ch}, {CHANNELS[ch]} nm)")
    ax1.legend(fontsize=8)
    ax2.axhline(0, color="grey", lw=0.8)
    ax2.plot(x, y - fit_y, "o")
    ax2.set_xlabel("Concentration (% v/v)")
    ax2.set_ylabel("Residual")
    fig.tight_layout()
    path = FIG_DIR / f"{name}_calibration_{ch}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 5. Simulated data (to test the pipeline before real data exists)
# ---------------------------------------------------------------------------
def simulate(concs=(0, 5, 10, 25, 50, 75, 100), repeats=3, seed=1):
    """
    Fake logger data for a dye that absorbs mainly in the blue-green.
    Includes dark offset, noise, and a slight curve at high absorbance
    (the finite-bandwidth effect), so the fit is realistic, not perfect.
    """
    rng = np.random.default_rng(seed)
    I0 = 30000 * np.exp(-((WL - 560) / 180) ** 2) + 3000       # blank counts (LED spectrum)
    dark = np.full(len(CH), 120.0)
    eps = 1.2 * np.exp(-((WL - 470) / 50) ** 2) + 0.03          # absorbance at 100 %
    rows = []
    for _ in range(10):
        rows.append(["dark", *(dark + rng.normal(0, 4, len(CH)))])
    for _ in range(10):
        rows.append(["blank", *(I0 + dark + rng.normal(0, 40, len(CH)))])
    for c in concs:
        if c == 0:
            continue
        A_true = eps * c / 100
        A_obs = A_true - 0.06 * A_true ** 2                     # bends at high A
        for _ in range(repeats):
            I = I0 * 10 ** (-A_obs) + dark + rng.normal(0, 40, len(CH))
            rows.append([f"c{c}", *I])
    return pd.DataFrame(rows, columns=["label"] + CH)


# ---------------------------------------------------------------------------
# 6. Run everything
# ---------------------------------------------------------------------------
def run(df, name, best_channel=None, min_blank=500):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    table, sd_blank_A = summarise(df)
    cal = calibrate(table, sd_blank_A)

    # A channel is only usable if enough light reached it on the blank.
    bc = blank_counts(df)
    usable = [ch for i, ch in enumerate(CH) if bc[i] >= min_blank]
    cal["blank_counts"] = [bc[CH.index(r["channel"])] for _, r in cal.iterrows()]
    cal["usable"] = cal["channel"].isin(usable)

    if best_channel is None:
        pick = cal[cal.usable]
        if pick.empty:
            pick = cal
            print(f"WARNING: no channel has >= {min_blank} blank counts. "
                  "Raise the gain or move the LED closer.")
        best_channel = pick.sort_values("slope_per_pct", ascending=False).iloc[0]["channel"]

    # Over-range warning: a sample whose counts approach the dark level is beyond
    # the stray-light limit, so its absorbance is a floor, not a measurement.
    dark = df.loc[df.label == "dark", CH].mean().values
    for _, r in table.iterrows():
        for i, ch in enumerate(CH):
            if ch not in usable:
                continue
            if r[f"A_{ch}"] > 0 and bc[i] > 0:
                frac = 10 ** (-r[f"A_{ch}"])
                if frac * bc[i] < max(20, 0.01 * bc[i]):
                    print(f"  over-range: {r['label']} on {ch} "
                          f"(A = {r[f'A_{ch}']:.2f} is at the stray-light floor)")

    pd.set_option("display.width", 140)
    print("\nMean absorbance per sample (first 6 channels shown):")
    print(table[["label", "conc", "n"] + [f"A_{c}" for c in CH[:6]]].round(4).to_string(index=False))
    print("\nCalibration per channel (usable = enough light on the blank):")
    print(cal.round(4).to_string(index=False))
    print(f"\nBest usable channel: {best_channel}")
    p1 = plot_spectra(table, name)
    p2 = plot_calibration(table, cal, best_channel, name)
    out_csv = FIG_DIR / f"{name}_calibration.csv"
    cal.to_csv(out_csv, index=False)
    print(f"\nSaved: {p1}\n       {p2}\n       {out_csv}")
    return table, cal


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        run(load_csv(path), path.stem)
    else:
        print("No file given, so running on SIMULATED data (demo).")
        run(simulate(), "simulated")
