from pathlib import Path
import random
import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PREVIEW_ROOT = PROJECT_ROOT / "processed" / "previews"
EVENT_FRAME_ROOT = PROJECT_ROOT / "processed" / "event_frames"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}

def preview_path(camera_name):
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    return PREVIEW_ROOT / f"{camera_name}.jpg"

def event_preview_path(camera_name):
    EVENT_FRAME_ROOT.mkdir(parents=True, exist_ok=True)
    return EVENT_FRAME_ROOT / f"{camera_name}_event.jpg"

def save_frame(camera_name, frame, event=False):
    path = event_preview_path(camera_name) if event else preview_path(camera_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), frame)
    return path

def save_first_or_last_frame_from_video(camera_name, video_path, mode="random"):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        idx = 0
    elif mode == "first":
        idx = 0
    elif mode == "last":
        idx = max(0, total - 1)
    else:
        idx = random.choice([0, max(0, total - 1)])
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    return save_frame(camera_name, frame, event=False)

def get_preview_for_camera(camera_name, prefer_event=True):
    event_path = event_preview_path(camera_name)
    if prefer_event and event_path.exists():
        return event_path
    path = preview_path(camera_name)
    if path.exists():
        return path
    return None
