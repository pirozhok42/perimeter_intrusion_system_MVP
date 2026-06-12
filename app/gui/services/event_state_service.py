import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVENT_STATE_PATH = PROJECT_ROOT / "processed" / "events" / "event_state.json"
EVENT_HISTORY_PATH = PROJECT_ROOT / "processed" / "events" / "event_history.json"

def _empty_state():
    return {"cameras": {}, "has_detection_alert": False, "has_tracking_alert": False, "has_summary_alert": False}

def load_event_state():
    if not EVENT_STATE_PATH.exists():
        return _empty_state()
    try:
        with open(EVENT_STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = _empty_state()
    state.setdefault("cameras", {})
    state.setdefault("has_detection_alert", False)
    state.setdefault("has_tracking_alert", False)
    state.setdefault("has_summary_alert", False)
    return state

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

def update_camera_event(camera_name, event_type, frame_path=None, log_path=None, video_path=None, module="detection"):
    state = load_event_state()
    cameras = state.setdefault("cameras", {})
    current = cameras.get(camera_name, {})
    current_module = current.get(module, {})

    severity = "alarm" if "ALARM" in event_type or "REID_PERSON_DETECTED" in event_type else "warning"
    if current_module.get("severity") == "alarm":
        severity = "alarm"

    current[module] = {
        "severity": severity,
        "event_type": event_type,
        "frame_path": frame_path or current_module.get("frame_path"),
        "log_path": log_path or current_module.get("log_path"),
        "video_path": video_path or current_module.get("video_path"),
        "acknowledged": False,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    cameras[camera_name] = current

    if module == "tracking":
        state["has_tracking_alert"] = True
    else:
        state["has_detection_alert"] = True
    state["has_summary_alert"] = True
    save_event_state(state)

    history = load_event_history()
    history.append({
        "camera_name": camera_name,
        "module": module,
        "severity": severity,
        "event_type": event_type,
        "frame_path": frame_path,
        "log_path": log_path,
        "video_path": video_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_event_history(history)

def get_camera_status(camera_name, module=None):
    camera_state = load_event_state().get("cameras", {}).get(camera_name, {})
    if module:
        return camera_state.get(module, {})
    return camera_state


def _clear_active_event(camera_module_state):
    camera_module_state["severity"] = None
    camera_module_state["event_type"] = None
    camera_module_state["frame_path"] = None
    camera_module_state["log_path"] = None
    camera_module_state["video_path"] = None
    camera_module_state["acknowledged"] = True


def acknowledge_camera(camera_name, module=None):
    state = load_event_state()
    cameras = state.setdefault("cameras", {})

    if camera_name in cameras:
        if module:
            if module in cameras[camera_name]:
                _clear_active_event(cameras[camera_name][module])
        else:
            for m in ["detection", "tracking"]:
                if m in cameras[camera_name]:
                    _clear_active_event(cameras[camera_name][m])

    state["has_detection_alert"] = any(bool(v.get("detection", {}).get("severity")) for v in cameras.values())
    state["has_tracking_alert"] = any(bool(v.get("tracking", {}).get("severity")) for v in cameras.values())
    state["has_summary_alert"] = state["has_detection_alert"] or state["has_tracking_alert"]
    save_event_state(state)

def acknowledge_summary_camera(camera_name, module=None):
    acknowledge_camera(camera_name, module)

def get_alert_flags():
    state = load_event_state()
    return bool(state.get("has_detection_alert")), bool(state.get("has_tracking_alert")), bool(state.get("has_summary_alert"))

def delete_history_records(indices):
    history = load_event_history()
    idx_set = set(indices)
    save_event_history([e for i, e in enumerate(history) if i not in idx_set])
