from pathlib import Path
import cv2
from PySide6.QtCore import QThread, Signal

from app.config import AppConfig
from app.pipeline import PerimeterPipeline
from app.video.video_io import list_videos, infer_camera_name_from_video
from app.gui.services.event_state_service import update_camera_event


class LiveProcessor(QThread):
    event_detected = Signal(str, str)
    processing_finished = Signal()

    def __init__(self, source="input_stream/live", default_config="configs/camera_1.json"):
        super().__init__()
        self.source = source
        self.default_config = default_config
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        videos = list_videos(self.source)

        for video in videos:
            if self._stop_requested:
                break

            camera_name = infer_camera_name_from_video(video, self.source)
            config_path = Path("configs") / f"{camera_name}.json"
            if not config_path.exists():
                config_path = Path(self.default_config)

            try:
                config = AppConfig.from_json(config_path)
                pipeline = PerimeterPipeline(config)
                result = pipeline.process_video(video)
                self._interpret_result(camera_name, video, result)
            except Exception as exc:
                print(f"Live processing error for {video}: {exc}")

        self.processing_finished.emit()

    def _interpret_result(self, camera_name: str, video_path: Path, result: dict):
        events_json = Path(result.get("events_json", ""))
        if not events_json.exists():
            return

        import json
        with open(events_json, "r", encoding="utf-8") as f:
            events = json.load(f)

        if not events:
            return

        # Alarm has priority
        alarm_events = [e for e in events if "ALARM" in e.get("event_type", "")]
        selected = alarm_events[0] if alarm_events else events[0]
        event_type = selected.get("event_type", "UNKNOWN_EVENT")
        frame_number = int(selected.get("frame", 0))

        frame_path = self._save_event_frame(camera_name, video_path, frame_number)
        update_camera_event(camera_name, event_type, str(frame_path) if frame_path else None, str(events_json))
        self.event_detected.emit(camera_name, event_type)

    def _save_event_frame(self, camera_name: str, video_path: Path, frame_number: int):
        output_dir = Path("processed") / "event_frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{camera_name}_event.jpg"

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, frame = cap.read()
        cap.release()

        if not ok:
            return None

        cv2.imwrite(str(output_path), frame)
        return output_path
