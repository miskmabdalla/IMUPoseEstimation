import os
import pandas as pd

def truncate_csvs_to_shortest_row_count(directory):
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    file_paths = [os.path.join(directory, f) for f in csv_files]

    if not file_paths:
        print("No CSV files found.")
        return

    # Find the minimum number of rows
    row_counts = {}
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        row_counts[file_path] = len(df)

    min_rows = min(row_counts.values())
    print(f"Minimum number of rows: {min_rows}")

    # Truncate and overwrite each file
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        truncated_df = df.iloc[:min_rows]
        truncated_df.to_csv(file_path, index=False)
        print(f"Truncated {os.path.basename(file_path)} to {min_rows} rows.")

# Example usage
truncate_csvs_to_shortest_row_count("dataset/imu_data/trial_14")
