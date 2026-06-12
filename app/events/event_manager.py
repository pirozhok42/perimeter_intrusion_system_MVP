from app.zones.geometry import point_in_polygon, bbox_touches_line, bbox_foot_point, line_side
from app.events.event_types import WARNING_STERILE_ZONE, ALARM_FENCE_CONTACT, ALARM_FENCE_CROSSED

class EventManager:
    def __init__(self, fence_line, sterile_zone, touch_threshold_px, dedup_seconds=1.0):
        self.fence_line = fence_line
        self.sterile_zone = sterile_zone
        self.touch_threshold_px = touch_threshold_px
        self.dedup_seconds = dedup_seconds
        self.last_side_by_track = {}
        self.last_event_time = {}

    def analyze_detection(self, xyxy, tracker_id, confidence, class_name, frame_idx, fps, camera_id):
        foot = bbox_foot_point(xyxy)
        in_zone = point_in_polygon(foot, self.sterile_zone)
        touches_fence = bbox_touches_line(xyxy, self.fence_line, self.touch_threshold_px)
        current_side = line_side(foot, self.fence_line)
        previous_side = self.last_side_by_track.get(tracker_id)
        crossed = previous_side is not None and current_side != 0 and previous_side != 0 and current_side != previous_side
        self.last_side_by_track[tracker_id] = current_side
        event_type = ALARM_FENCE_CROSSED if crossed else ALARM_FENCE_CONTACT if touches_fence else WARNING_STERILE_ZONE if in_zone else None
        if event_type is None:
            return None
        time_sec = frame_idx / fps if fps else 0
        key = (tracker_id, event_type)
        if key in self.last_event_time and time_sec - self.last_event_time[key] < self.dedup_seconds:
            return None
        self.last_event_time[key] = time_sec
        return {
            "timestamp_sec": round(time_sec, 3),
            "frame": int(frame_idx),
            "camera_id": camera_id,
            "object_id": int(tracker_id),
            "class_name": class_name,
            "confidence_score": round(float(confidence), 4),
            "event_type": event_type,
            "foot_point_x": int(foot[0]),
            "foot_point_y": int(foot[1])
        }
