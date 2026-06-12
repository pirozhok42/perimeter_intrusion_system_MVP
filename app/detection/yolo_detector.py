import supervision as sv
from ultralytics import YOLO

class YoloDetector:
    def __init__(self, weights, confidence_threshold, iou_threshold, enabled_class_ids):
        self.model = YOLO(weights)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.enabled_class_ids = enabled_class_ids

    def detect(self, frame):
        result = self.model(frame, conf=self.confidence_threshold, iou=self.iou_threshold, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        if len(detections) == 0:
            return detections
        mask = [int(cid) in self.enabled_class_ids for cid in detections.class_id]
        return detections[mask]
