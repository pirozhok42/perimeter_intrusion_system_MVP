from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox, QFrame
from app.gui.services.camera_service import create_camera

class AddCameraPage(QWidget):
    def __init__(self, on_camera_created=None):
        super().__init__()
        self.on_camera_created = on_camera_created
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32,32,32,32)
        layout.setSpacing(16)
        title = QLabel("Добавить камеру")
        title.setObjectName("Title")
        desc = QLabel("Для детекции: per / ter. Для мультикамерного трекинга: trk.")
        desc.setObjectName("Subtitle")
        desc.setWordWrap(True)
        self.role_select = QComboBox()
        self.role_select.addItems(["Детекция забора", "Мультикамерный трекинг"])
        self.role_select.currentTextChanged.connect(self._on_role_changed)
        self.location_select = QComboBox()
        self.location_select.addItems(["Периметр", "Территория"])
        self.camera_name_input = QLineEdit()
        self.camera_name_input.setPlaceholderText("per_cam_1, ter_cam_1 или trk_cam_1")
        btn = QPushButton("Создать камеру")
        btn.clicked.connect(self._create_camera)
        self.status = QLabel("")
        self.status.setObjectName("Subtitle")
        self.status.setWordWrap(True)
        for w in [title, desc, QLabel("Назначение камеры"), self.role_select, QLabel("Расположение"), self.location_select, QLabel("Название камеры"), self.camera_name_input, btn, self.status]:
            if isinstance(w, QLabel) and w.text() in ["Назначение камеры", "Расположение", "Название камеры"]:
                w.setObjectName("SectionTitle")
            layout.addWidget(w)
        layout.addStretch()
        root.addWidget(card)
        self._on_role_changed(self.role_select.currentText())

    def _on_role_changed(self, value):
        if value == "Мультикамерный трекинг":
            self.location_select.setCurrentText("Территория")
            self.location_select.setEnabled(False)
            self.camera_name_input.setPlaceholderText("Например: trk_cam_1")
        else:
            self.location_select.setEnabled(True)
            self.camera_name_input.setPlaceholderText("Например: per_cam_1 или ter_cam_1")

    def _create_camera(self):
        app_role = "tracking" if self.role_select.currentText() == "Мультикамерный трекинг" else "detection"
        camera_type = "territory" if app_role == "tracking" else "perimeter" if self.location_select.currentText().lower() == "периметр" else "territory"
        try:
            result = create_camera(self.camera_name_input.text(), camera_type, app_role)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        QMessageBox.information(self, "Загрузка тестового видео", f"Загрузите видео:\n\n{result['archive_path']}\n\nLive:\n\n{result['live_path']}")
        QMessageBox.information(self, "Камера создана", f"Камера «{result['camera_name']}» создана.")
        self.status.setText(f"Создано: {result['archive_path']}")
        if self.on_camera_created:
            self.on_camera_created(result["camera_name"])
