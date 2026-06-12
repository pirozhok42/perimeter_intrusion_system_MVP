from pathlib import Path
import time
import cv2
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtCore import QThread, Signal

from app.video.video_io import list_videos, infer_camera_name_from_video
from app.gui.services.event_state_service import update_camera_event
from app.reid.global_id_manager import GlobalIdManager


class LiveProcessor(QThread):
    event_detected = Signal(str, str)
    processing_finished = Signal()
    status_message = Signal(str)

    def __init__(
        self,
        source="input_stream/live",
        default_config="configs/camera_1.json",
        poll_seconds=3.0,
        processing_mode="two_streams",
    ):
        super().__init__()
        self.source = source
        self.default_config = default_config
        self.poll_seconds = poll_seconds
        self.processing_mode = processing_mode
        self._stop_requested = False
        self._processed = set()
        self.shared_reid_manager = GlobalIdManager(similarity_threshold=0.72)

    def stop(self):
        self._stop_requested = True

    def run(self):
        mode_name = {
            "single_thread": "1 поток",
            "two_streams": "2 потока: детекция + трекинг",
            "per_camera": "потоки по количеству камер",
        }.get(self.processing_mode, self.processing_mode)

        self.status_message.emit(f"Обработка live: запущена ({mode_name}), ожидание новых видео")

        while not self._stop_requested:
            try:
                videos = list_videos(self.source)
            except Exception as exc:
                print(f"Live scan error: {exc}")
                videos = []

            new_videos = []
            for video in videos:
                key = str(Path(video).resolve())
                if key not in self._processed:
                    self._processed.add(key)
                    new_videos.append(video)

            if new_videos:
                self._process_batch(new_videos)

            time.sleep(self.poll_seconds)

        self.status_message.emit("Обработка live: пауза")
        self.processing_finished.emit()

    def _process_batch(self, videos):
        if self.processing_mode == "single_thread":
            for video in videos:
                if self._stop_requested:
                    return
                self._process_video_safe(video)
            return

        if self.processing_mode == "two_streams":
            detection_videos = []
            tracking_videos = []

            for video in videos:
                camera_name = infer_camera_name_from_video(video, self.source)
                if camera_name.startswith("trk"):
                    tracking_videos.append(video)
                else:
                    detection_videos.append(video)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                if detection_videos:
                    futures.append(executor.submit(self._process_list, detection_videos))
                if tracking_videos:
                    futures.append(executor.submit(self._process_list, tracking_videos))

                for future in as_completed(futures):
                    if self._stop_requested:
                        return
                    future.result()
            return

        if self.processing_mode == "per_camera":
            groups = {}
            for video in videos:
                camera_name = infer_camera_name_from_video(video, self.source)
                groups.setdefault(camera_name, []).append(video)

            max_workers = max(1, len(groups))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._process_list, cam_videos) for cam_videos in groups.values()]
                for future in as_completed(futures):
                    if self._stop_requested:
                        return
                    future.result()
            return

        for video in videos:
            self._process_video_safe(video)

    def _process_list(self, videos):
        for video in videos:
            if self._stop_requested:
                return
            self._process_video_safe(video)

    def _process_video_safe(self, video):
        try:
            self._process_video(video)
        except Exception as exc:
            print(f"Live processing error for {video}: {exc}")

    def _process_video(self, video):
        # Heavy imports are intentionally lazy, so GUI can open even if torch stack is broken.
        from app.config import AppConfig
        from app.pipeline import PerimeterPipeline
        from app.reid.reid_pipeline import ReIdPipeline

        camera_name = infer_camera_name_from_video(video, self.source)
        config_path = Path("configs") / f"{camera_name}.json"
        if not config_path.exists():
            config_path = Path(self.default_config)

        self.status_message.emit(f"Обработка live: {camera_name}")

        config = AppConfig.from_json(config_path)

        if config.raw.get("app_role") == "tracking" or camera_name.startswith("trk"):
            pipeline = ReIdPipeline(config, global_id_manager=self.shared_reid_manager)
        else:
            pipeline = PerimeterPipeline(config)

        result = pipeline.process_video(video)
        self._interpret_result(camera_name, Path(video), result)

    def _interpret_result(self, camera_name, video_path, result):
        import json

        events_json = Path(result.get("events_json", ""))
        if not events_json.exists():
            return

        with open(events_json, "r", encoding="utf-8") as f:
            events = json.load(f)

        if not events:
            return

        alarm_events = [e for e in events if "ALARM" in e.get("event_type", "")]
        selected = alarm_events[0] if alarm_events else events[0]
        event_type = selected.get("event_type", "UNKNOWN_EVENT")
        frame_number = int(selected.get("frame", 0))

        frame_path = self._save_event_frame(camera_name, video_path, frame_number)
        module = "tracking" if camera_name.startswith("trk") else "detection"

        update_camera_event(
            camera_name,
            event_type,
            str(frame_path) if frame_path else None,
            str(events_json),
            str(video_path),
            module=module,
        )

        self.event_detected.emit(camera_name, event_type)

    def _save_event_frame(self, camera_name, video_path, frame_number):
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
