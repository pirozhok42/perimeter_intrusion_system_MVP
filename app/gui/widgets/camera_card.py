from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from app.gui.services.event_state_service import get_camera_status


class CameraCard(QFrame):
    delete_requested = Signal(str)
    edit_lines_requested = Signal(str)
    acknowledge_requested = Signal(str)

    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.camera_name = camera["name"]
        self.app_role = camera.get("app_role", "detection")
        self.module = "tracking" if self.app_role == "tracking" else "detection"

        status = get_camera_status(self.camera_name, self.module)
        severity = status.get("severity")

        if severity == "alarm":
            self.setObjectName("CameraCardAlarm")
        elif severity == "warning":
            self.setObjectName("CameraCardWarning")
        else:
            self.setObjectName("CameraCard")

        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self._build_ui(status)

    def _build_ui(self, status):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title_text = self.camera_name
        if self.app_role == "tracking":
            title_text += "  · tracking"

        title = QLabel(title_text)
        title.setObjectName("SectionTitle")
        title.setAlignment(Qt.AlignCenter)

        preview = QLabel()
        preview.setFixedHeight(170)
        preview.setAlignment(Qt.AlignCenter)

        preview_path = self.camera.get("preview_frame")
        if preview_path:
            pixmap = QPixmap(str(preview_path))
            if not pixmap.isNull():
                preview.setPixmap(pixmap.scaled(320, 170, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self._set_no_video(preview)
        else:
            self._set_no_video(preview)

        layout.addWidget(title)
        layout.addWidget(preview)

        if status.get("severity") and status.get("event_type"):
            event_label = QLabel(f"Событие: {status.get('event_type')}")
            event_label.setObjectName("Subtitle")
            event_label.setWordWrap(True)
            layout.addWidget(event_label)

        buttons = QHBoxLayout()

        if self.app_role != "tracking":
            line_text = "Редактировать линии" if self.camera.get("is_configured") else "Добавить линии"
            line_btn = QPushButton(line_text)
            line_btn.clicked.connect(lambda: self.edit_lines_requested.emit(self.camera_name))
            buttons.addWidget(line_btn, 1)
        else:
            info = QLabel("Камера трекинга: разметка линий не требуется")
            info.setObjectName("Subtitle")
            info.setWordWrap(True)
            buttons.addWidget(info, 1)

        delete_btn = QPushButton("🗑")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.camera_name))
        buttons.addWidget(delete_btn)

        layout.addLayout(buttons)

        if status.get("severity"):
            ok_btn = QPushButton("Ок")
            ok_btn.setObjectName("SecondaryButton")
            ok_btn.clicked.connect(lambda: self.acknowledge_requested.emit(self.camera_name))
            layout.addWidget(ok_btn)

    def _set_no_video(self, label):
        label.setObjectName("NoVideo")
        label.setText("NO VIDEO")
