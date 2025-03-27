import os
import subprocess
from pathlib import Path

def reduce_fps(input_path, output_path, target_fps=50):
    """
    Reduces video frame rate to `target_fps` using ffmpeg.

    Args:
        input_path (str | Path): Path to the input video file.
        output_path (str | Path): Path to the output video file.
        target_fps (int): Target frame rate (default: 50).
    """
    input_path = str(input_path)
    output_path = str(output_path)

    command = f'ffmpeg -y -i "{input_path}" -filter:v fps={target_fps} "{output_path}"'
    print(f"▶️ Reducing FPS: {input_path} → {output_path}")

    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def convert_directory_60_to_50fps(input_dir="videos_data/60_fps", output_dir="videos_data/50_fps"):
    """
    Converts all videos in `input_dir` to 50 fps and saves to `output_dir`.

    Args:
        input_dir (str | Path): Directory containing source 60 fps videos.
        output_dir (str | Path): Output directory for 50 fps converted videos.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    supported_exts = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

    for video in input_dir.glob("*"):
        if video.suffix.lower() in supported_exts:
            output_path = output_dir / video.name
            reduce_fps(video, output_path, target_fps=50)

convert_directory_60_to_50fps()