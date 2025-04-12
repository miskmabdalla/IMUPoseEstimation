import os
import subprocess
from pathlib import Path

def convert_mov_to_mp4_in_place(input_dir):
    """
    Converts all .MOV files in the directory to .mp4 format using ffmpeg.
    Saves the .mp4 files in the same directory and deletes the original .MOV files
    only if conversion succeeded and output file is valid.
    """
    input_dir = Path(input_dir)
    for mov_file in input_dir.iterdir():
        if mov_file.is_file() and mov_file.suffix.lower() == ".mov":
            mp4_file = mov_file.with_suffix(".mp4")
            print(f"\n[DEBUG] MOV: {mov_file.resolve()}")
            print(f"[DEBUG] MP4: {mp4_file.resolve()}")
            command = f'ffmpeg -y -i "{mov_file}" -c:v libx264 -an "{mp4_file}"'
            result = subprocess.run(command, shell=True, capture_output=True)
            
            if result.returncode != 0:
                print(f"[ERROR] ffmpeg failed for {mov_file.name}:\n{result.stderr.decode()}")
            elif mp4_file.exists() and mp4_file.stat().st_size > 0:
                print(f"[SUCCESS] Created {mp4_file.name}")
                mov_file.unlink()
                print(f"[INFO] Deleted original: {mov_file.name}")
            else:
                print(f"[WARNING] Output not found or empty: {mp4_file.name}")
        else:
            print(f"[SKIP] Not a .MOV file: {mov_file.name}")

def reduce_fps(input_path, output_path, target_fps=50):
    """
    Reduces video frame rate to `target_fps` using ffmpeg.
    """
    input_path = str(input_path)
    output_path = str(output_path)
    command = f'ffmpeg -y -i "{input_path}" -filter:v fps={target_fps} "{output_path}"'
    print(f"[INFO] Reducing FPS: {input_path} --> {output_path}")
    result = subprocess.run(command, shell=True, capture_output=True)
    
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg failed on FPS reduction:\n{result.stderr.decode()}")
    elif Path(output_path).exists() and Path(output_path).stat().st_size > 0:
        print(f"[SUCCESS] FPS reduction complete: {output_path}")
    else:
        print(f"[WARNING] Failed to produce valid output: {output_path}")

def convert_directory_60_to_50fps(input_dir="videos_data/60_fps", output_dir="videos_data/50_fps"):
    """
    Converts all videos in `input_dir` to 50 fps and saves them in `output_dir`.
    Converts .MOV files to .mp4 in-place first.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Processing directory: {input_dir.resolve()}")
    if not input_dir.exists():
        print("[ERROR] Input directory does not exist.")
        return

    print(f"[INFO] Input contents: {[f.name for f in input_dir.iterdir()]}")

    convert_mov_to_mp4_in_place(input_dir)

    supported_exts = [".mp4"]
    for video in input_dir.iterdir():
        if video.is_file() and video.suffix.lower() in supported_exts:
            output_path = output_dir / video.name
            reduce_fps(video, output_path, target_fps=50)
        else:
            print(f"[SKIP] Not an MP4 file: {video.name}")

# Run conversion
convert_directory_60_to_50fps()