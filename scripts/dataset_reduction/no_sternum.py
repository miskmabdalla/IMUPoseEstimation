import os
import shutil
import pandas as pd

# Define input and output base directories
input_root = 'dataset/final_dataset'
output_root = 'dataset/reduced_dataset/dataset_no_sternum'

# Ensure output root directory exists
os.makedirs(output_root, exist_ok=True)

# Iterate through each trial_X folder
for folder_name in os.listdir(input_root):
    input_folder = os.path.join(input_root, folder_name)

    if os.path.isdir(input_folder) and folder_name.startswith("trial_"):
        input_X_csv = os.path.join(input_folder, "X.csv")
        input_Y_csv = os.path.join(input_folder, "Y.csv")

        if os.path.isfile(input_X_csv):
            print(f"Processing: {input_X_csv}")

            try:
                # Load and reduce X.csv
                df_X = pd.read_csv(input_X_csv)
                chest_cols = [col for col in df_X.columns if 'chest' in col.lower()]
                df_X.drop(columns=chest_cols, inplace=True)

                # Prepare output directory and paths
                output_folder = os.path.join(output_root, folder_name)
                os.makedirs(output_folder, exist_ok=True)

                output_X_csv = os.path.join(output_folder, "X.csv")
                output_Y_csv = os.path.join(output_folder, "Y.csv")

                # Save reduced X.csv
                df_X.to_csv(output_X_csv, index=False)
                print(f"  Saved reduced X.csv to: {output_X_csv}")
                print(f"  Removed columns: {chest_cols}")

                # Copy Y.csv unchanged
                if os.path.isfile(input_Y_csv):
                    shutil.copy2(input_Y_csv, output_Y_csv)
                    print(f"  Copied Y.csv to: {output_Y_csv}")
                else:
                    print(f"  Y.csv not found in: {input_folder}")

            except Exception as e:
                print(f"  Error processing {input_folder}: {e}")
        else:
            print(f"  X.csv not found in: {input_folder}")
