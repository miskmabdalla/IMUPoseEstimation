import os
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator

# === Config ===
STEP_MS = 20  # sampling interval in ms
INPUT_ROOT = Path("dataset/intermediate_data/imu_data")
OUTPUT_ROOT = Path("dataset/intermediate_data/sync_imu_data")
SENSOR_MAP_CSV = Path("sensors_order.csv")

# === Load sensor role mapping ===
sensor_map_df = pd.read_csv(SENSOR_MAP_CSV)
sensor_mapping = dict(zip(sensor_map_df["mac_address"], sensor_map_df["sensor_role"]))
sensor_roles = list(sensor_mapping.values())

# === Helpers ===
def load_csv(file_path):
    df = pd.read_csv(file_path, sep='\t', engine='python')
    df.columns = [col.strip() for col in df.columns]
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.astype(float)
    df = df.sort_values("Millis").reset_index(drop=True)
    return df

def interpolate_sensor(df, common_time):
    result = pd.DataFrame({'Millis': common_time})
    for col in df.columns:
        if col == "Millis":
            continue
        valid = ~df[col].isna()
        if valid.sum() < 2:
            result[col] = np.nan
            continue
        f = PchipInterpolator(df["Millis"][valid], df[col][valid], extrapolate=False)
        result[col] = f(common_time)
    return result

def rename_columns(df, role):
    return df.rename(columns={col: f"{col}_{role}" for col in df.columns if col != "Millis"})

def process_trial(trial_path: Path, output_path: Path):
    dfs_by_role = {}

    for file_path in trial_path.glob("*.csv"):
        mac = file_path.stem  # assumes filename is just MAC without prefix
        if mac not in sensor_mapping:
            continue
        role = sensor_mapping[mac]
        df = load_csv(file_path)
        dfs_by_role[role] = df

    if len(dfs_by_role) < 2:
        print(f"Skipping {trial_path.name}: not enough matching sensors.")
        return

    # Determine common time grid
    start_time = max(df["Millis"].min() for df in dfs_by_role.values())
    end_time = min(df["Millis"].max() for df in dfs_by_role.values())
    common_time = np.arange(start_time, end_time, STEP_MS)

    # Interpolate and merge in consistent order
    merged_df = pd.DataFrame({'Millis': common_time})
    for role in sensor_roles:
        if role not in dfs_by_role:
            continue
        interp_df = interpolate_sensor(dfs_by_role[role], common_time)
        interp_df = rename_columns(interp_df, role)
        merged_df = pd.concat([merged_df, interp_df.drop(columns=["Millis"])], axis=1)

    merged_df = merged_df.round(3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")

# === Run all trials ===
for trial_dir in INPUT_ROOT.glob("trial_*"):
    output_file = OUTPUT_ROOT / f"{trial_dir.name}.csv"
    process_trial(trial_dir, output_file)
