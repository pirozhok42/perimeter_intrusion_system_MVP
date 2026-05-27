from pathlib import Path
import cv2

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}

def list_videos(source):
    source = Path(source)
    if source.is_file():
        return [source]
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    return [p for p in sorted(source.iterdir()) if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]

def make_video_writer(output_path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
