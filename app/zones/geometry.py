import math
import cv2
import numpy as np

def point_in_polygon(point, polygon):
    if not polygon:
        return False
    return cv2.pointPolygonTest(np.array(polygon, dtype=np.int32), point, False) >= 0

def point_line_distance(point, line):
    if not line or len(line) != 2:
        return 10**9
    px, py = point
    (x1, y1), (x2, y2) = line
    line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if line_len_sq == 0:
        return math.hypot(px-x1, py-y1)
    t = ((px-x1)*(x2-x1)+(py-y1)*(y2-y1))/line_len_sq
    t = max(0, min(1, t))
    proj_x = x1 + t*(x2-x1)
    proj_y = y1 + t*(y2-y1)
    return math.hypot(px-proj_x, py-proj_y)

def line_side(point, line):
    if not line or len(line) != 2:
        return 0
    px, py = point
    (x1, y1), (x2, y2) = line
    value = (x2-x1)*(py-y1) - (y2-y1)*(px-x1)
    return 1 if value > 0 else -1 if value < 0 else 0

def bbox_foot_point(xyxy):
    x1, y1, x2, y2 = xyxy
    return int((x1+x2)/2), int(y2)

def bbox_touches_line(xyxy, line, threshold_px):
    return point_line_distance(bbox_foot_point(xyxy), line) <= threshold_px
