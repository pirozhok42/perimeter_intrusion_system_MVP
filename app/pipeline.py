from pathlib import Path
import cv2
from tqdm import tqdm
from app.detection.yolo_detector import YoloDetector
from app.tracking.bytetrack_tracker import ByteTrackTracker
from app.events.event_manager import EventManager
from app.events.logger import EventLogger
from app.visualization.draw import Visualizer
from app.video.video_io import make_video_writer

class PerimeterPipeline:
    def __init__(self, config):
        self.config = config
        self.detector = YoloDetector(
            config.model_weights,
            config.confidence_threshold,
            config.iou_threshold,
            config.enabled_class_ids
        )
        self.class_name_by_id = config.class_name_by_id
        self.visualizer = Visualizer(config.fence_line, config.sterile_zone)

    def process_video(self, video_path):
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.config.output_videos_dir.mkdir(parents=True, exist_ok=True)
        self.config.output_logs_dir.mkdir(parents=True, exist_ok=True)

        out_video = self.config.output_videos_dir / f"{video_path.stem}_annotated.mp4"
        out_csv = self.config.output_logs_dir / f"{video_path.stem}_events.csv"
        out_json = self.config.output_logs_dir / f"{video_path.stem}_events.json"

        writer = make_video_writer(out_video, fps, width, height)
        tracker = ByteTrackTracker()
        event_manager = EventManager(
            self.config.fence_line,
            self.config.sterile_zone,
            self.config.fence_touch_threshold_px,
            self.config.dedup_seconds
        )
        logger = EventLogger()

        frame_idx = 0
        PROCESS_EVERY_N_FRAMES = 5
        last_detections = None
        with tqdm(total=total_frames if total_frames > 0 else None, desc=f"Processing {video_path.name}") as pbar:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if frame_idx % PROCESS_EVERY_N_FRAMES == 0:
                    detections = self.detector.detect(frame)
                    detections = tracker.update(detections)
                    last_detections = detections
                else:
                    detections = last_detections

                annotated = self.visualizer.draw_zones(frame)
                labels = []

                for i in range(len(detections)):
                    xyxy = detections.xyxy[i].astype(int)
                    tracker_id = int(detections.tracker_id[i]) if detections.tracker_id is not None else -1
                    class_id = int(detections.class_id[i]) if detections.class_id is not None else -1
                    class_name = self.class_name_by_id.get(class_id, str(class_id))
                    conf = float(detections.confidence[i]) if detections.confidence is not None else 0.0

                    event = event_manager.analyze_detection(
                        xyxy=xyxy,
                        tracker_id=tracker_id,
                        confidence=conf,
                        class_name=class_name,
                        frame_idx=frame_idx,
                        fps=fps,
                        camera_id=self.config.camera_id
                    )

                    label = f"ID {tracker_id} {class_name} {conf:.2f}"
                    if event:
                        logger.add(event)
                        label += f" | {event['event_type']}"
                    labels.append(label)

                annotated = self.visualizer.draw_detections(annotated, detections, labels)
                writer.write(annotated)
                frame_idx += 1
                pbar.update(1)

        cap.release()
        writer.release()
        logger.save(out_csv, out_json)

        return {
            "input_video": str(video_path),
            "output_video": str(out_video),
            "events_csv": str(out_csv),
            "events_json": str(out_json),
            "events_count": len(logger.events)
        }
