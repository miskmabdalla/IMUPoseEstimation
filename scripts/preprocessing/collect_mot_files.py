import os
import shutil

SOURCE_ROOT = 'Sports2D_results'
DEST_DIR = 'dataset/intermediate_data/angles_data/mot_files'

# Ensure destination directory exists
os.makedirs(DEST_DIR, exist_ok=True)

for folder_name in os.listdir(SOURCE_ROOT):
    folder_path = os.path.join(SOURCE_ROOT, folder_name)
    if not os.path.isdir(folder_path):
        continue

    # Example: trial_4_Sports2D
    if not folder_name.endswith('_Sports2D'):
        continue

    trial_name = folder_name.replace('_Sports2D', '')
    expected_prefix = f"{folder_name}_angles_person00.mot"
    mot_file_path = os.path.join(folder_path, expected_prefix)

    if not os.path.exists(mot_file_path):
        print(f".mot file not found in {folder_path}")
        continue

    new_filename = f"{trial_name}.mot"
    dest_path = os.path.join(DEST_DIR, new_filename)

    shutil.move(mot_file_path, dest_path)
    print(f"Moved: {mot_file_path} --> {dest_path}")
