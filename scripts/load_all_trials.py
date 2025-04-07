import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import matplotlib.pyplot as plt

def align_sequences(X, y):
    if X.shape[0] > y.shape[0]:
        X = X[:y.shape[0]]
    elif y.shape[0] > X.shape[0]:
        delta = y.shape[0] - X.shape[0]
        cut_start = delta // 2
        cut_end = delta - cut_start
        y = y[cut_start: -cut_end if cut_end > 0 else None]
    return X, y

def load_and_preprocess_all_trials(imu_root, angles_root, window_size):
    X_all, y_all = [], []

    imu_root = Path(imu_root)
    angles_root = Path(angles_root)

    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    imu_stack = []
    angle_stack = []

    for trial_folder in sorted(imu_root.iterdir()):
        if not trial_folder.is_dir():
            continue

        trial_id = trial_folder.name
        print(f"[INFO] Processing {trial_id}")

        # Load and combine all IMU CSVs
        imu_dfs = []
        for imu_file in sorted(trial_folder.glob("*.csv")):
            df = pd.read_csv(imu_file)
            df = df.drop(columns=[df.columns[0]])  # Drop timestamp
            imu_dfs.append(df)

        if not imu_dfs:
            print(f"[WARN] No IMU files in {trial_id}")
            continue

        # Truncate each IMU file to shortest length
        imu_lengths = [len(df) for df in imu_dfs]
        min_len = min(imu_lengths)
        imu_concat = pd.concat([df.iloc[:min_len] for df in imu_dfs], axis=1).values

        # Find matching angle file
        angle_file = angles_root / f"{trial_id}.csv"
        if not angle_file.exists():
            print(f"[WARN] Missing angles file for {trial_id}")
            continue

        angle_df = pd.read_csv(angle_file)
        angle_df = angle_df.drop(columns=[col for col in angle_df.columns if 'time' in col.lower()])
        angle_data = angle_df.iloc[:min_len].values

        # Align
        imu_data, angle_data = align_sequences(imu_concat, angle_data)

        imu_stack.append(imu_data)
        angle_stack.append(angle_data)

    if not imu_stack or not angle_stack:
        raise RuntimeError("No valid trials found with aligned IMU and angle data.")

    # Global scale
    imu_stacked = np.vstack(imu_stack)
    angle_stacked = np.vstack(angle_stack)

    imu_scaled = scaler_X.fit_transform(imu_stacked)
    angle_scaled = scaler_y.fit_transform(angle_stacked)

    # Re-split and window
    idx = 0
    for imu_data, angle_data in zip(imu_stack, angle_stack):
        length = len(imu_data)
        imu_scaled_part = imu_scaled[idx:idx+length]
        angle_scaled_part = angle_scaled[idx:idx+length]
        idx += length

        for i in range(length - window_size + 1):
            X_all.append(imu_scaled_part[i:i+window_size])
            y_all.append(angle_scaled_part[i + window_size - 1])

    print(f"[INFO] Finished processing. Total sequences: {len(X_all)}")
    return np.array(X_all), np.array(y_all), scaler_X, scaler_y