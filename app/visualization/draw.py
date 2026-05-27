import cv2
import numpy as np
import supervision as sv
from app.zones.geometry import bbox_foot_point

class Visualizer:
    def __init__(self, fence_line, sterile_zone):
        self.fence_line = fence_line
        self.sterile_zone = sterile_zone
        self.box_annotator = sv.BoxAnnotator(thickness=2)
        self.label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.5)

    def draw_zones(self, frame):
        annotated = frame.copy()
        zone_np = np.array(self.sterile_zone, dtype=np.int32)
        overlay = annotated.copy()
        cv2.fillPoly(overlay, [zone_np], color=(0, 255, 255))
        annotated = cv2.addWeighted(overlay, 0.18, annotated, 0.82, 0)
        cv2.polylines(annotated, [zone_np], isClosed=True, color=(0, 255, 255), thickness=2)
        cv2.line(annotated, tuple(self.fence_line[0]), tuple(self.fence_line[1]), (0, 0, 255), 3)
        return annotated

    def draw_detections(self, frame, detections, labels):
        if len(detections) == 0:
            return frame
        annotated = self.box_annotator.annotate(scene=frame, detections=detections)
        annotated = self.label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
        for xyxy in detections.xyxy:
            cv2.circle(annotated, bbox_foot_point(xyxy.astype(int)), 5, (255, 0, 0), -1)
        return annotated
