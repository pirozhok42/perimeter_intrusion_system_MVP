from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton


class CameraCard(QFrame):
    delete_requested = Signal(str)
    edit_lines_requested = Signal(str)

    def __init__(self, camera: dict):
        super().__init__()
        self.camera = camera
        self.camera_name = camera["name"]
        self.setObjectName("CameraCard")
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel(self.camera_name)
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

        buttons = QHBoxLayout()

        line_text = "Редактировать линии" if self.camera.get("is_configured") else "Добавить линии"
        line_btn = QPushButton(line_text)
        line_btn.clicked.connect(lambda: self.edit_lines_requested.emit(self.camera_name))

        delete_btn = QPushButton("🗑")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.camera_name))

        buttons.addWidget(line_btn, 1)
        buttons.addWidget(delete_btn)

        layout.addWidget(title)
        layout.addWidget(preview)
        layout.addLayout(buttons)

    def _set_no_video(self, label):
        label.setObjectName("NoVideo")
        label.setText("NO VIDEO")
