from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class AppConfig:
    raw: dict

    @classmethod
    def from_json(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @property
    def camera_id(self): return self.raw.get("camera_id", "camera_1")
    @property
    def model_weights(self): return self.raw["model"].get("weights", "yolov8n.pt")
    @property
    def confidence_threshold(self): return float(self.raw["model"].get("confidence_threshold", 0.35))
    @property
    def iou_threshold(self): return float(self.raw["model"].get("iou_threshold", 0.5))
    @property
    def enabled_class_ids(self):
        classes = self.raw["model"].get("classes", {})
        enabled = self.raw["model"].get("enabled_classes", ["person"])
        return [int(classes[name]) for name in enabled if name in classes]
    @property
    def class_name_by_id(self):
        return {int(v): k for k, v in self.raw["model"].get("classes", {}).items()}
    @property
    def fence_line(self): return self.raw.get("zones", {}).get("fence_line", [])
    @property
    def sterile_zone(self): return self.raw.get("zones", {}).get("sterile_zone", [])
    @property
    def fence_touch_threshold_px(self): return float(self.raw.get("zones", {}).get("fence_touch_threshold_px", 12))
    @property
    def output_videos_dir(self): return Path(self.raw.get("output", {}).get("videos_dir", "processed/videos"))
    @property
    def output_logs_dir(self): return Path(self.raw.get("output", {}).get("logs_dir", "processed/logs"))
    @property
    def dedup_seconds(self): return float(self.raw.get("events", {}).get("dedup_seconds", 1.0))
