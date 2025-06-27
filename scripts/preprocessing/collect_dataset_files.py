import shutil
from pathlib import Path

# === Paths ===
WRAPPED_Y_ROOT = Path("dataset/intermediate_data/wrapped_angles")
ALIGNED_X_ROOT = Path("dataset/intermediate_data/aligned_dataset")
OUTPUT_ROOT = Path("dataset/final_dataset")

# === Function ===
def copy_trial_files(trial_name: str):
    src_y = WRAPPED_Y_ROOT / trial_name / "Y.csv"
    src_x = ALIGNED_X_ROOT / trial_name / "X.csv"
    dst_dir = OUTPUT_ROOT / trial_name

    if not src_y.exists():
        print(f"Missing Y.csv in {src_y}")
        return
    if not src_x.exists():
        print(f"Missing X.csv in {src_x}")
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_y, dst_dir / "Y.csv")
    shutil.copy2(src_x, dst_dir / "X.csv")

    print(f"Copied X and Y for {trial_name} to {dst_dir}")

# === Main Execution ===
for trial_dir in sorted(WRAPPED_Y_ROOT.glob("trial_*")):
    if not trial_dir.is_dir():
        continue
    trial_name = trial_dir.name
    copy_trial_files(trial_name)

print("Dataset collection complete.")
