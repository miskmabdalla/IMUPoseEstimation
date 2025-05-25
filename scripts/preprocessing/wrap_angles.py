import pandas as pd
from pathlib import Path

# Root folder containing all trial folders
aligned_data_root = Path("aligned_dataset")

# Loop over all trials
for trial_dir in sorted(aligned_data_root.glob("trial_*")):
    y_path = trial_dir / "Y.csv"
    if not y_path.exists():
        print(f"⚠️ Y.csv missing in {trial_dir}, skipping.")
        continue

    print(f"Processing {y_path}")

    # Load the Y.csv
    y_df = pd.read_csv(y_path)

    # Drop time column if it exists
    y_df = y_df.drop(columns=["time"], errors="ignore")

    # ─── wrap every angle column into the interval [0, +180°] ──
    # (Assumes all remaining columns are joint‐angle columns in degrees.)
    y_df.loc[:, :] = abs(((y_df + 180) % 360) - 180)
    # ───────────────────────────────────────────────────────────────

    # Save back to the same file (overwriting)
    y_df.to_csv(y_path, index=False)

print("✅ All Y.csv files processed and corrected with mod 180.")
