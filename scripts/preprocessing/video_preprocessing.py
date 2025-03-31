import os
import subprocess
from pathlib import Path

def convert_mov_to_mp4_in_place(input_dir):
    """
    Converts all .mov files in the directory to .mp4 format using ffmpeg.
    Saves the .mp4 files in the same directory and deletes the original .mov files.
    """
    input_dir = Path(input_dir)
    for mov_file in input_dir.glob("*.mov"):
        mp4_file = mov_file.with_suffix(".mp4")
        command = f'ffmpeg -y -i "{mov_file}" -c:v libx264 -c:a aac "{mp4_file}"'
        print(f"🎥 Converting MOV to MP4: {mov_file.name} → {mp4_file.name}")
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mov_file.unlink()  # delete original .mov file


def reduce_fps(input_path, output_path, target_fps=50):
    """
    Reduces video frame rate to `target_fps` using ffmpeg.
    """
    input_path = str(input_path)
    output_path = str(output_path)
    command = f'ffmpeg -y -i "{input_path}" -filter:v fps={target_fps} "{output_path}"'
    print(f"▶️ Reducing FPS: {input_path} → {output_path}")
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def convert_directory_60_to_50fps(input_dir="videos_data/60_fps", output_dir="videos_data/50_fps"):
    """
    Converts all videos in `input_dir` to 50 fps and saves them in `output_dir`.
    Prior to that, it converts all .mov files to .mp4 in-place.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    convert_mov_to_mp4_in_place(input_dir)

    supported_exts = [".mp4"]
    for video in input_dir.glob("*"):
        if video.suffix.lower() in supported_exts:
            output_path = output_dir / video.name
            reduce_fps(video, output_path, target_fps=50)


# Run conversion
convert_directory_60_to_50fps()
