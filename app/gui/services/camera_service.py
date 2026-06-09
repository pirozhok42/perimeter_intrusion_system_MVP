import json
import re
import shutil
from pathlib import Path
import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_ROOT = PROJECT_ROOT / "input_stream" / "live"
ARCHIVE_ROOT = PROJECT_ROOT / "input_stream" / "archive"
CONFIG_ROOT = PROJECT_ROOT / "configs"
PREVIEW_ROOT = PROJECT_ROOT / "processed" / "previews"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v"}


def sanitize_camera_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ_-]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        raise ValueError("Название камеры не может быть пустым")
    return name


def validate_camera_name(camera_name: str, camera_type: str) -> str:
    safe = sanitize_camera_name(camera_name)
    prefix = "per" if camera_type == "perimeter" else "ter"

    if not safe.startswith(prefix):
        raise ValueError(f"Название камеры должно начинаться с «{prefix}»")

    if camera_exists(safe):
        raise ValueError(f"Камера с названием «{safe}» уже существует")

    return safe


def camera_exists(camera_name: str) -> bool:
    return (
        (LIVE_ROOT / camera_name).exists()
        or (ARCHIVE_ROOT / camera_name).exists()
        or (CONFIG_ROOT / f"{camera_name}.json").exists()
    )


def create_camera(camera_name: str, camera_type: str) -> dict:
    safe_name = validate_camera_name(camera_name, camera_type)

    live_path = LIVE_ROOT / safe_name
    archive_path = ARCHIVE_ROOT / safe_name
    config_path = CONFIG_ROOT / f"{safe_name}.json"

    live_path.mkdir(parents=True, exist_ok=False)
    archive_path.mkdir(parents=True, exist_ok=False)
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)

    config = default_camera_config(safe_name, camera_type)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return {
        "camera_name": safe_name,
        "camera_type": camera_type,
        "live_path": live_path,
        "archive_path": archive_path,
        "config_path": config_path,
    }


def default_camera_config(camera_name: str, camera_type: str) -> dict:
    return {
        "camera_id": camera_name,
        "camera_type": camera_type,
        "is_configured": False,
        "model": {
            "weights": "yolov8n.pt",
            "confidence_threshold": 0.35,
            "iou_threshold": 0.5,
            "classes": {
                "person": 0,
                "car": 2,
                "motorcycle": 3,
                "bus": 5,
                "truck": 7
            },
            "enabled_classes": ["person"]
        },
        "zones": {
            "fence_line": [],
            "sterile_zone": [],
            "fence_touch_threshold_px": 12
        },
        "events": {
            "dedup_seconds": 1.0
        },
        "output": {
            "videos_dir": "processed/videos",
            "logs_dir": "processed/logs"
        }
    }


def list_cameras(camera_type: str | None = None) -> list[dict]:
    cameras = {}
    for base in [LIVE_ROOT, ARCHIVE_ROOT]:
        base.mkdir(parents=True, exist_ok=True)
        for p in sorted(base.iterdir()):
            if p.is_dir():
                cameras[p.name] = p.name

    result = []
    for name in sorted(cameras.keys()):
        ctype = "perimeter" if name.startswith("per") else "territory" if name.startswith("ter") else "unknown"
        if camera_type and ctype != camera_type:
            continue
        result.append({
            "name": name,
            "camera_type": ctype,
            "live_path": LIVE_ROOT / name,
            "archive_path": ARCHIVE_ROOT / name,
            "config_path": CONFIG_ROOT / f"{name}.json",
            "is_configured": is_camera_configured(name),
            "preview_frame": get_camera_preview_frame(name),
        })
    return result


def is_camera_configured(camera_name: str) -> bool:
    config_path = CONFIG_ROOT / f"{camera_name}.json"
    if not config_path.exists():
        return False
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        zones = config.get("zones", {})
        return bool(config.get("is_configured")) and len(zones.get("fence_line", [])) == 2 and len(zones.get("sterile_zone", [])) == 4
    except Exception:
        return False


def find_first_video(camera_name: str) -> Path | None:
    for base in [ARCHIVE_ROOT / camera_name, LIVE_ROOT / camera_name]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                return path
    return None


def get_camera_preview_frame(camera_name: str) -> Path | None:
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = PREVIEW_ROOT / f"{camera_name}.jpg"

    video_path = find_first_video(camera_name)
    if video_path is None:
        return None

    cap = cv2.VideoCapture(str(video_path))
    ok, frame = cap.read()
    cap.release()

    if not ok:
        return None

    cv2.imwrite(str(out_path), frame)
    return out_path


def delete_camera(camera_name: str):
    for path in [
        LIVE_ROOT / camera_name,
        ARCHIVE_ROOT / camera_name,
        CONFIG_ROOT / f"{camera_name}.json",
        PREVIEW_ROOT / f"{camera_name}.jpg",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def save_camera_zones(camera_name: str, fence_line: list, sterile_zone: list):
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    config_path = CONFIG_ROOT / f"{camera_name}.json"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        ctype = "perimeter" if camera_name.startswith("per") else "territory"
        config = default_camera_config(camera_name, ctype)

    config["camera_id"] = camera_name
    config["is_configured"] = True
    config.setdefault("zones", {})
    config["zones"]["fence_line"] = fence_line
    config["zones"]["sterile_zone"] = sterile_zone
    config["zones"].setdefault("fence_touch_threshold_px", 12)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config_path
