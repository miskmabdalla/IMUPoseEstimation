from pathlib import Path
import pandas as pd

# === Config ===
INPUT_ROOT = Path("dataset/intermediate_data/aligned_dataset")
OUTPUT_ROOT = Path("dataset/intermediate_data/wrapped_angles")

# === Helpers ===
def wrap_angles(df):
    cols_to_wrap = [col for col in df.columns if col.lower() != "time"]
    df[cols_to_wrap] = ((df[cols_to_wrap] + 180) % 360) - 180
    return df

def process_y_file(input_y_path: Path, output_y_path: Path):
    df = pd.read_csv(input_y_path)
    df = df.drop(columns=["time"], errors="ignore")
    df = wrap_angles(df)

    output_y_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_y_path, index=False)
    print(f"Saved wrapped Y.csv to {output_y_path}")

# === Process all trial folders ===
for trial_dir in sorted(INPUT_ROOT.glob("trial_*")):
    input_y_path = trial_dir / "Y.csv"
    if not input_y_path.exists():
        print(f"Y.csv missing in {trial_dir.name}, skipping.")
        continue

    output_y_path = OUTPUT_ROOT / trial_dir.name / "Y.csv"
    process_y_file(input_y_path, output_y_path)

print("All Y.csv files wrapped and saved.")
