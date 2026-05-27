import argparse
from pathlib import Path
import cv2

parser = argparse.ArgumentParser()
parser.add_argument("--video", required=True)
parser.add_argument("--out", default="processed/configs/first_frame.jpg")
args = parser.parse_args()

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(args.video)
ok, frame = cap.read()
cap.release()

if not ok:
    raise RuntimeError(f"Could not read first frame from {args.video}")

cv2.imwrite(str(out), frame)
print(f"Saved: {out}")
