#!/bin/bash

# Exit immediately on error
set -e

# Directory containing preprocessing scripts
SCRIPT_DIR="scripts/preprocessing"

# Ordered list of script base names (without .py)
SCRIPTS=(
  "video_preprocessing"
  "video_renaming"
  "run_sports2d_batch"
  "collect_mot_files"
  "mot_to_csv"
  "normalize_imu"
  "synchronize_imu_data"
  "align_imu_angles"
  "wrap_angles"
)

echo "🚀 Starting preprocessing pipeline..."

# Loop through and run each script
for script in "${SCRIPTS[@]}"; do
  echo "🔧 Running $script.py..."
  python "$SCRIPT_DIR/$script.py"
  echo "✅ Finished $script.py"
done

echo "🎉 All preprocessing scripts completed successfully."
