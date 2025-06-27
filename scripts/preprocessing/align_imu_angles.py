import os
from pathlib import Path
import pandas as pd

# === Config ===
IMU_ROOT = Path("dataset/intermediate_data/sync_imu_data")
ANGLES_ROOT = Path("dataset/intermediate_data/angles_data/csv_files")
OUTPUT_ROOT = Path("dataset/intermediate_data/aligned_dataset")

# === Helpers ===
def load_csv(path):
    return pd.read_csv(path)

def trim_to_match(imu_df, angle_df):
    len_imu = len(imu_df)
    len_angle = len(angle_df)

    if len_imu > len_angle:
        imu_df = imu_df.iloc[:len_angle].reset_index(drop=True)
    elif len_angle > len_imu:
        excess = len_angle - len_imu
        front = excess // 2
        back = excess - front
        angle_df = angle_df.iloc[front:len_angle - back].reset_index(drop=True)

    return imu_df, angle_df

# === Process all trials ===
for imu_file in sorted(IMU_ROOT.glob("trial_*.csv")):
    trial_name = imu_file.stem
    angles_file = ANGLES_ROOT / f"{trial_name}.csv"
    if not angles_file.exists():
        print(f"Missing angles for {trial_name}, skipping.")
        continue

    imu_df = load_csv(imu_file)
    angle_df = load_csv(angles_file)

    imu_trimmed, angle_trimmed = trim_to_match(imu_df, angle_df)

    output_trial_dir = OUTPUT_ROOT / trial_name
    output_trial_dir.mkdir(parents=True, exist_ok=True)

    imu_trimmed.to_csv(output_trial_dir / "X.csv", index=False)
    angle_trimmed.to_csv(output_trial_dir / "Y.csv", index=False)

    print(f"Aligned trial saved to {output_trial_dir}")