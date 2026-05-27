import argparse
import json
from pathlib import Path
import cv2
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True)
parser.add_argument("--config", default="configs/camera_1.json")
parser.add_argument("--out", default="processed/configs/config_preview.jpg")
args = parser.parse_args()

image = cv2.imread(args.image)
if image is None:
    raise RuntimeError(f"Could not read image: {args.image}")

with open(args.config, "r", encoding="utf-8") as f:
    config = json.load(f)

fence_line = config["zones"]["fence_line"]
sterile_zone = config["zones"]["sterile_zone"]

zone_np = np.array(sterile_zone, dtype=np.int32)
overlay = image.copy()
cv2.fillPoly(overlay, [zone_np], color=(0, 255, 255))
image = cv2.addWeighted(overlay, 0.25, image, 0.75, 0)
cv2.polylines(image, [zone_np], isClosed=True, color=(0, 255, 255), thickness=3)
cv2.line(image, tuple(fence_line[0]), tuple(fence_line[1]), (0, 0, 255), 4)

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(out), image)
print(f"Saved: {out}")
