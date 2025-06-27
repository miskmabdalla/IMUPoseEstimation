#!/usr/bin/env python3
"""
Plot every cleaned Y.csv in dataset/final_dataset/trial_*.

For each trial:
• A 4x6 grid of joint-angle plots is generated.
• The figure is saved as trial_X_angles.png inside the same folder.
• The figure window is displayed (comment plt.show() if running headless).
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ─── configuration ──────────────────────────────────────────────────
ROOT          = Path("dataset/final_dataset")   # parent folder of trial_* dirs
N_ROWS, N_COLS = 4, 6                     # grid layout (N_ROWS * N_COLS ≥ #columns)
SAVE_PNG       = True                     # set False if you do not want image files
# ────────────────────────────────────────────────────────────────────


def plot_trial(y_path: Path, n_rows: int, n_cols: int, save_png: bool) -> None:
    """Plot all columns of one Y.csv as a grid of subplots."""
    df = pd.read_csv(y_path).drop(columns=["time"], errors="ignore")
    n_plots = df.shape[1]
    assert n_rows * n_cols >= n_plots, "Grid too small for number of joints"

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 2.5),
                             sharex=True)
    axes = axes.flatten()

    time = range(len(df))

    for idx, col in enumerate(df.columns):
        ax = axes[idx]
        ax.plot(time, df[col])
        ax.set_title(col, fontsize=8)
        ax.set_ylabel("deg")
        ax.tick_params(axis="both", labelsize=7)

    # hide unused axes if grid > n_plots
    for ax in axes[n_plots:]:
        ax.set_visible(False)

    fig.suptitle(y_path.parent.name, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    # if save_png:
    #     png_path = y_path.with_name(f"{y_path.parent.name}_angles.png")
    #     fig.savefig(png_path, dpi=150)
    #     print(f"    ⇢ Saved {png_path.name}")

    plt.show()   # comment out if you run this in a non-GUI environment
    plt.close(fig)


def main() -> None:
    trials = sorted(ROOT.glob("trial_*"))
    if not trials:
        print(f"No trial_* folders found in {ROOT.resolve()}")
        return

    for trial_dir in trials:
        y_path = trial_dir / "Y.csv"
        if not y_path.exists():
            print(f" {y_path.relative_to(ROOT.parent)} missing, skipping.")
            continue

        print(f"Plotting {y_path.relative_to(ROOT.parent)}")
        plot_trial(y_path, N_ROWS, N_COLS, SAVE_PNG)


if __name__ == "__main__":
    main()