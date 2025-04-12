import os

def rename_files_in_directory(directory):
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"{directory} is not a valid directory")

    # List all files (not directories)
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    # Sort files by name (ascending)
    files.sort()

    # Rename files to trial_X, preserving file extension
    for index, filename in enumerate(files, start=1):
        old_path = os.path.join(directory, filename)
        file_ext = os.path.splitext(filename)[1]
        new_name = f"trial_{index}{file_ext}"
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} --> {new_name}")

target_directory = "videos_data/50_fps"
rename_files_in_directory(target_directory)
