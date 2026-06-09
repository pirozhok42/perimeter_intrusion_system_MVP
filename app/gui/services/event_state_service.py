import json
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVENT_STATE_PATH = PROJECT_ROOT / "processed" / "events" / "event_state.json"
EVENT_FRAMES_ROOT = PROJECT_ROOT / "processed" / "event_frames"


def load_event_state() -> dict:
    if not EVENT_STATE_PATH.exists():
        return {"cameras": {}, "has_perimeter_alert": False, "has_summary_alert": False}
    try:
        with open(EVENT_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"cameras": {}, "has_perimeter_alert": False, "has_summary_alert": False}


def save_event_state(state: dict):
    EVENT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clear_event_state():
    save_event_state({"cameras": {}, "has_perimeter_alert": False, "has_summary_alert": False})


def update_camera_event(camera_name: str, event_type: str, frame_path: str | None = None, log_path: str | None = None):
    state = load_event_state()
    cameras = state.setdefault("cameras", {})

    severity = "alarm" if "ALARM" in event_type else "warning"

    current = cameras.get(camera_name, {})
    if current.get("severity") == "alarm":
        severity = "alarm"

    cameras[camera_name] = {
        "severity": severity,
        "event_type": event_type,
        "frame_path": frame_path or current.get("frame_path"),
        "log_path": log_path or current.get("log_path"),
    }

    state["has_perimeter_alert"] = True
    state["has_summary_alert"] = True
    save_event_state(state)


def get_camera_status(camera_name: str) -> dict:
    return load_event_state().get("cameras", {}).get(camera_name, {})


def get_alert_flags() -> tuple[bool, bool]:
    state = load_event_state()
    return bool(state.get("has_perimeter_alert")), bool(state.get("has_summary_alert"))
