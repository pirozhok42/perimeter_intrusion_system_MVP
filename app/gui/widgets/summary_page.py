import json
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout

from app.gui.services.camera_service import list_cameras
from app.gui.services.event_state_service import get_camera_status


class SummaryPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(14)

        title = QLabel("Сводка")
        title.setObjectName("Title")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.grid_holder = QWidget()
        self.grid = QGridLayout(self.grid_holder)
        self.grid.setSpacing(16)

        self.scroll.setWidget(self.grid_holder)

        layout.addWidget(title)
        layout.addWidget(self.scroll)

        root.addWidget(card)
        self.refresh()

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        cameras = list_cameras()

        if not cameras:
            empty = QLabel("Камер пока нет.")
            empty.setObjectName("Subtitle")
            self.grid.addWidget(empty, 0, 0)
            return

        for idx, camera in enumerate(cameras):
            box = self._make_camera_summary_box(camera["name"])
            self.grid.addWidget(box, idx // 2, idx % 2)

    def _make_camera_summary_box(self, camera_name: str):
        status = get_camera_status(camera_name)
        severity = status.get("severity")

        box = QFrame()
        if severity == "alarm":
            box.setObjectName("AlarmCard")
        elif severity == "warning":
            box.setObjectName("WarningCard")
        else:
            box.setObjectName("CameraCard")

        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        title = QLabel(camera_name)
        title.setObjectName("SectionTitle")

        event_type = status.get("event_type", "Событий не обнаружено")
        event_label = QLabel(f"Последнее событие: {event_type}")
        event_label.setObjectName("Subtitle")
        event_label.setWordWrap(True)

        details = QLabel(self._load_log_summary(status.get("log_path")))
        details.setObjectName("Subtitle")
        details.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(event_label)
        layout.addWidget(details)
        layout.addStretch()

        return box

    def _load_log_summary(self, log_path):
        if not log_path:
            return "Логи пока отсутствуют."

        path = Path(log_path)
        if not path.exists():
            return "Лог-файл не найден."

        try:
            with open(path, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception:
            return "Не удалось прочитать лог."

        if not events:
            return "Событий нет."

        warnings = sum(1 for e in events if "WARNING" in e.get("event_type", ""))
        alarms = sum(1 for e in events if "ALARM" in e.get("event_type", ""))
        last = events[-1]
        return (
            f"Всего событий: {len(events)}\\n"
            f"Предупреждения: {warnings}\\n"
            f"Тревоги: {alarms}\\n"
            f"Последнее время: {last.get('timestamp_sec', last.get('time_sec', '?'))} сек."
        )
