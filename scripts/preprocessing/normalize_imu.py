import os
import pandas as pd

# Base directory containing all trial folders
BASE_DIR = "dataset/intermediate_data/imu_data"

def normalize_millis_in_csv(file_path):
    try:
        # Read the CSV, skipping the first column (row index)
        df = pd.read_csv(file_path, sep=',', engine='python')
        
        # Ensure required columns are present
        if "Millis" not in df.columns:
            print(f"'Millis' column missing in {file_path}")
            return

        # Normalize the 'Millis' column
        df["Millis"] = df["Millis"] - df["Millis"].iloc[0]

        # Save back to the same file (preserve tab separator and header)
        df.to_csv(file_path, sep='\t', index=False)
        print(f"Normalized: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def normalize_all_trials(base_dir):
    if not os.path.exists(base_dir):
        print(f"Directory does not exist: {base_dir}")
        return

    for trial_folder in os.listdir(base_dir):
        trial_path = os.path.join(base_dir, trial_folder)
        if not os.path.isdir(trial_path):
            continue

        for file in os.listdir(trial_path):
            if file.endswith(".csv"):
                csv_path = os.path.join(trial_path, file)
                normalize_millis_in_csv(csv_path)

# Run normalization on all trial folders
normalize_all_trials(BASE_DIR)
