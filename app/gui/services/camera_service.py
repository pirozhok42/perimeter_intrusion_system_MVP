import json, re, shutil
from pathlib import Path
import cv2
from app.gui.services.preview_service import get_preview_for_camera, save_first_or_last_frame_from_video

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_ROOT = PROJECT_ROOT / "input_stream" / "live"
ARCHIVE_ROOT = PROJECT_ROOT / "input_stream" / "archive"
CONFIG_ROOT = PROJECT_ROOT / "configs"
PREVIEW_ROOT = PROJECT_ROOT / "processed" / "previews"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}

def sanitize_camera_name(name):
    name = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ_-]+", "_", name.strip().lower())
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        raise ValueError("Название камеры не может быть пустым")
    return name

def camera_exists(camera_name):
    return (LIVE_ROOT / camera_name).exists() or (ARCHIVE_ROOT / camera_name).exists() or (CONFIG_ROOT / f"{camera_name}.json").exists()

def validate_camera_name(camera_name, camera_type, app_role="detection"):
    safe = sanitize_camera_name(camera_name)
    prefix = "trk" if app_role == "tracking" else "per" if camera_type == "perimeter" else "ter"
    if not safe.startswith(prefix):
        raise ValueError(f"Название камеры должно начинаться с «{prefix}»")
    if camera_exists(safe):
        raise ValueError(f"Камера с названием «{safe}» уже существует")
    return safe

def default_camera_config(camera_name, camera_type, app_role="detection"):
    return {
        "camera_id": camera_name,
        "camera_type": "territory" if app_role == "tracking" else camera_type,
        "app_role": app_role,
        "is_configured": app_role == "tracking",
        "model": {
            "weights": "yolo11s.pt",
            "confidence_threshold": 0.35,
            "iou_threshold": 0.5,
            "classes": {"person": 0, "car": 2, "motorcycle": 3, "bus": 5, "truck": 7},
            "enabled_classes": ["person"]
        },
        "reid": {
            "enabled": app_role == "tracking",
            "model_name": "mobilenet_v3_large",
            "weights": "mobilenet_v3_large.pth",
            "similarity_threshold": 0.62,
            "device": "cuda",
            "reid_update_every_n_frames": 10
        },
        "zones": {"fence_line": [], "sterile_zone": [], "fence_touch_threshold_px": 12},
        "events": {"dedup_seconds": 1.0},
        "output": {"videos_dir": "processed/videos", "logs_dir": "processed/logs"}
    }

def create_camera(camera_name, camera_type, app_role="detection"):
    safe = validate_camera_name(camera_name, camera_type, app_role)
    live_path = LIVE_ROOT / safe
    archive_path = ARCHIVE_ROOT / safe
    config_path = CONFIG_ROOT / f"{safe}.json"
    live_path.mkdir(parents=True, exist_ok=False)
    archive_path.mkdir(parents=True, exist_ok=False)
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(default_camera_config(safe, camera_type, app_role), f, ensure_ascii=False, indent=2)
    return {"camera_name": safe, "camera_type": "territory" if app_role == "tracking" else camera_type, "app_role": app_role, "live_path": live_path, "archive_path": archive_path, "config_path": config_path}

def _read_config(camera_name):
    p = CONFIG_ROOT / f"{camera_name}.json"
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def list_cameras(camera_type=None, app_role=None):
    cameras = {}
    for base in [LIVE_ROOT, ARCHIVE_ROOT]:
        base.mkdir(parents=True, exist_ok=True)
        for p in sorted(base.iterdir()):
            if p.is_dir():
                cameras[p.name] = p.name

    result = []
    for name in sorted(cameras):
        cfg = _read_config(name)
        role = cfg.get("app_role") or ("tracking" if name.startswith("trk") else "detection")
        ctype = cfg.get("camera_type") or ("perimeter" if name.startswith("per") else "territory" if name.startswith("ter") else "tracking")
        if camera_type and ctype != camera_type:
            continue
        if app_role and role != app_role:
            continue
        result.append({
            "name": name,
            "camera_type": ctype,
            "app_role": role,
            "live_path": LIVE_ROOT / name,
            "archive_path": ARCHIVE_ROOT / name,
            "config_path": CONFIG_ROOT / f"{name}.json",
            "is_configured": is_camera_configured(name),
            "preview_frame": get_camera_preview_frame(name),
        })
    return result

def is_camera_configured(camera_name):
    cfg = _read_config(camera_name)
    if cfg.get("app_role") == "tracking":
        return True
    zones = cfg.get("zones", {})
    return bool(cfg.get("is_configured")) and len(zones.get("fence_line", [])) == 2 and len(zones.get("sterile_zone", [])) == 4

def find_first_video(camera_name):
    for base in [ARCHIVE_ROOT / camera_name, LIVE_ROOT / camera_name]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                return path
    return None


def get_camera_preview_frame(camera_name):
    existing = get_preview_for_camera(camera_name, prefer_event=True)
    if existing:
        return existing

    video = find_first_video(camera_name)
    if not video:
        return None

    return save_first_or_last_frame_from_video(camera_name, video, mode="first")

def delete_camera(camera_name):
    for p in [LIVE_ROOT/camera_name, ARCHIVE_ROOT/camera_name, CONFIG_ROOT/f"{camera_name}.json", PREVIEW_ROOT/f"{camera_name}.jpg", PROJECT_ROOT/"processed"/"event_frames"/f"{camera_name}_event.jpg"]:
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

def save_camera_zones(camera_name, fence_line, sterile_zone):
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    p = CONFIG_ROOT / f"{camera_name}.json"
    cfg = _read_config(camera_name) or default_camera_config(camera_name, "perimeter", "detection")
    cfg["camera_id"] = camera_name
    cfg["is_configured"] = True
    cfg.setdefault("zones", {})
    cfg["zones"]["fence_line"] = fence_line
    cfg["zones"]["sterile_zone"] = sterile_zone
    cfg["zones"].setdefault("fence_touch_threshold_px", 12)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return p
