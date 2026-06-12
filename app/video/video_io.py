from pathlib import Path
import cv2

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}

def list_videos(source):
    source = Path(source)
    if source.is_file():
        return [source]
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    return [p for p in sorted(source.rglob("*")) if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]

def infer_camera_name_from_video(video_path, source_root=None):
    video_path = Path(video_path)
    if source_root:
        try:
            rel = video_path.relative_to(Path(source_root))
            if len(rel.parts) >= 2:
                return rel.parts[0]
        except ValueError:
            pass
    return video_path.parent.name

def make_video_writer(output_path, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
