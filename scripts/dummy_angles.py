import pandas as pd
import numpy as np
import os

# Define the headers based on the original CSV
headers = [
    'time', 'right ankle', 'left ankle', 'right knee', 'left knee', 'right hip', 'left hip',
    'right shoulder', 'left shoulder', 'right elbow', 'left elbow', 'right foot', 'left foot',
    'right shank', 'left shank', 'right thigh', 'left thigh', 'pelvis', 'trunk', 'shoulders',
    'head', 'right arm', 'left arm', 'right forearm', 'left forearm'
]

def generate_random_csv(num_rows: int, filename: str):
    output_dir = "dataset/angles_data/csv_files"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # Generate data: time as increasing float, other values are random
    data = {
        headers[0]: np.linspace(0, num_rows - 1, num_rows)
    }
    for col in headers[1:]:
        data[col] = np.random.rand(num_rows)

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Generated CSV with {num_rows} rows at: {output_path}")

# Example usage
generate_random_csv(num_rows=552, filename="trial_14.csv")
