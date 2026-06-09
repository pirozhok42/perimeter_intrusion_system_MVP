from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QFrame
)

from app.gui.services.camera_service import create_camera


class AddCameraPage(QWidget):
    def __init__(self, on_camera_created=None):
        super().__init__()
        self.on_camera_created = on_camera_created
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QLabel("Добавить камеру")
        title.setObjectName("Title")

        description = QLabel(
            "Для камеры периметра название должно начинаться с «per». "
            "Для камеры территории — с «ter». Одинаковые названия запрещены."
        )
        description.setObjectName("Subtitle")
        description.setWordWrap(True)

        location_label = QLabel("Выберите расположение камеры")
        location_label.setObjectName("SectionTitle")

        self.location_select = QComboBox()
        self.location_select.addItems(["Периметр", "Территория"])

        name_label = QLabel("Напишите или придумайте название камеры")
        name_label.setObjectName("SectionTitle")

        self.camera_name_input = QLineEdit()
        self.camera_name_input.setPlaceholderText("Например: per_cam_1 или ter_cam_1")

        self.create_button = QPushButton("Создать камеру")
        self.create_button.clicked.connect(self._create_camera)

        self.status = QLabel("")
        self.status.setObjectName("Subtitle")
        self.status.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(8)
        layout.addWidget(location_label)
        layout.addWidget(self.location_select)
        layout.addWidget(name_label)
        layout.addWidget(self.camera_name_input)
        layout.addWidget(self.create_button)
        layout.addWidget(self.status)
        layout.addStretch()

        root.addWidget(card)

    def _create_camera(self):
        location = self.location_select.currentText().lower()
        camera_type = "perimeter" if location == "периметр" else "territory"

        try:
            result = create_camera(self.camera_name_input.text(), camera_type)
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        except FileExistsError:
            QMessageBox.warning(self, "Ошибка", "Камера с таким названием уже существует.")
            return

        live_path = result["live_path"]
        archive_path = result["archive_path"]
        camera_name = result["camera_name"]

        QMessageBox.information(
            self,
            "Загрузка тестового видео",
            "Загрузите тестовое видео с камеры для дальнейшей настройки по пути:\n\n"
            f"{archive_path}\n\n"
            "Для live-имитации используйте путь:\n\n"
            f"{live_path}"
        )

        QMessageBox.information(
            self,
            "Камера создана",
            f"Камера «{camera_name}» создана."
        )

        self.status.setText(f"Создано:\narchive: {archive_path}\nlive: {live_path}")

        if self.on_camera_created:
            self.on_camera_created(camera_name)
