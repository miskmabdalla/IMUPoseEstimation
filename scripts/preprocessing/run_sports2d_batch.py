import os
import toml
from Sports2D import Sports2D

# === CONFIGURATION ===
CONFIG_TEMPLATE_PATH = 'Config_Sports2D.toml'
TEMP_CONFIG_PATH = 'Config_TEMP.toml'
VIDEO_DIR = 'videos_data/50_fps'
RESULT_DIR = 'Sports2D_results'
VALID_EXTENSIONS = ('.mp4', '.avi', '.mov')
SKIP_ALREADY_PROCESSED = True  # Set to False if you always want to reprocess

def is_already_processed(video_file):
    """
    Check if a result folder like trial_X_Sports2D/ already exists.
    """
    basename = os.path.splitext(os.path.basename(video_file))[0]
    expected_folder = os.path.join(RESULT_DIR, f'{basename}_Sports2D')
    return os.path.isdir(expected_folder)

def run_sports2d_batch():
    # Load the base config once
    try:
        base_config = toml.load(CONFIG_TEMPLATE_PATH)
    except Exception as e:
        print(f"Failed to load base config: {CONFIG_TEMPLATE_PATH}")
        print(e)
        return

    # List video files
    video_files = sorted([
        f for f in os.listdir(VIDEO_DIR)
        if f.endswith(VALID_EXTENSIONS)
    ])

    if not video_files:
        print(f"No video files found in: {VIDEO_DIR}")
        return

    for video_filename in video_files:
        video_path = video_filename
        basename = os.path.splitext(video_filename)[0]

        if SKIP_ALREADY_PROCESSED and is_already_processed(video_path):
            print(f"Skipping (already processed): {video_filename}")
            continue

        print(f"Processing: {video_filename}")

        # Inject video path into config
        config = base_config.copy()
        config['project']['video_input'] = video_path

        # Write temporary config file
        try:
            with open(TEMP_CONFIG_PATH, 'w') as f:
                toml.dump(config, f)
        except Exception as e:
            print(f"Failed to write temp config for: {video_filename}")
            print(e)
            continue

        # Run Sports2D
        try:
            Sports2D.process(TEMP_CONFIG_PATH)
            print(f"Finished: {video_filename}")
        except Exception as e:
            print(f"Failed to process: {video_filename}")
            print(e)


run_sports2d_batch()
