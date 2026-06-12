import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVENT_STATE_PATH = PROJECT_ROOT / "processed" / "events" / "event_state.json"
EVENT_HISTORY_PATH = PROJECT_ROOT / "processed" / "events" / "event_history.json"

def _empty_state():
    return {"cameras": {}, "has_perimeter_alert": False, "has_summary_alert": False}

def load_event_state():
    if not EVENT_STATE_PATH.exists():
        return _empty_state()
    try:
        with open(EVENT_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _empty_state()

def save_event_state(state):
    EVENT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_event_history():
    if not EVENT_HISTORY_PATH.exists():
        return []
    try:
        with open(EVENT_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_event_history(history):
    EVENT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def update_camera_event(camera_name, event_type, frame_path=None, log_path=None, video_path=None):
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
        "video_path": video_path or current.get("video_path"),
        "acknowledged": False,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    state["has_perimeter_alert"] = True
    state["has_summary_alert"] = True
    save_event_state(state)
    history = load_event_history()
    history.append({
        "camera_name": camera_name,
        "severity": severity,
        "event_type": event_type,
        "frame_path": frame_path,
        "log_path": log_path,
        "video_path": video_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_event_history(history)

def get_camera_status(camera_name):
    return load_event_state().get("cameras", {}).get(camera_name, {})

def acknowledge_camera(camera_name):
    state = load_event_state()
    cameras = state.setdefault("cameras", {})
    if camera_name in cameras:
        cameras[camera_name]["severity"] = None
        cameras[camera_name]["acknowledged"] = True
    any_alert = any(bool(v.get("severity")) for v in cameras.values())
    state["has_perimeter_alert"] = any_alert
    state["has_summary_alert"] = any_alert
    save_event_state(state)

def acknowledge_summary_camera(camera_name):
    acknowledge_camera(camera_name)

def get_alert_flags():
    state = load_event_state()
    return bool(state.get("has_perimeter_alert")), bool(state.get("has_summary_alert"))


def delete_history_records(indices: list[int]):
    history = load_event_history()
    index_set = set(indices)
    new_history = [event for idx, event in enumerate(history) if idx not in index_set]
    save_event_history(new_history)
