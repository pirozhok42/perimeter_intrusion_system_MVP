from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QFrame, QScrollArea, QGridLayout

from app.gui.services.camera_service import list_cameras, delete_camera
from app.gui.services.event_state_service import acknowledge_camera
from app.gui.widgets.camera_card import CameraCard
from app.gui.widgets.zone_editor_dialog import ZoneEditorDialog


class CameraListPage(QWidget):
    def __init__(self, section: str):
        super().__init__()
        self.section = section  # "perimeter" or "territory"
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("Card")

        self.layout = QVBoxLayout(self.card)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(14)

        self.title = QLabel("Камеры периметра" if self.section == "perimeter" else "Камеры территории")
        self.title.setObjectName("Title")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.grid_holder = QWidget()
        self.grid = QGridLayout(self.grid_holder)
        self.grid.setSpacing(16)

        self.scroll.setWidget(self.grid_holder)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.scroll)

        root.addWidget(self.card)
        self.refresh()

    def _get_cameras(self):
        if self.section == "perimeter":
            # Только камеры детекции периметра.
            return list_cameras(camera_type="perimeter", app_role="detection")

        # Территория = обычные territory-камеры + tracking-камеры.
        territory_detection = list_cameras(camera_type="territory", app_role="detection")
        tracking_cameras = list_cameras(app_role="tracking")
        return territory_detection + tracking_cameras

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        cameras = self._get_cameras()

        if not cameras:
            empty = QLabel("Камер пока нет.")
            empty.setObjectName("Subtitle")
            self.grid.addWidget(empty, 0, 0)
            return

        for idx, camera in enumerate(cameras):
            card = CameraCard(camera)
            card.delete_requested.connect(self._delete_camera)
            card.edit_lines_requested.connect(self._edit_lines)
            card.acknowledge_requested.connect(self._acknowledge_camera)
            row = idx // 3
            col = idx % 3
            self.grid.addWidget(card, row, col)

    def _acknowledge_camera(self, camera_name: str):
        module = "tracking" if camera_name.startswith("trk") else "detection"
        acknowledge_camera(camera_name, module)
        self.refresh()

    def _delete_camera(self, camera_name: str):
        result = QMessageBox.question(
            self,
            "Удалить камеру",
            f"Удалить камеру «{camera_name}» вместе с папками и конфигом?"
        )
        if result != QMessageBox.Yes:
            return

        delete_camera(camera_name)
        self.refresh()

    def _edit_lines(self, camera_name: str):
        if camera_name.startswith("trk"):
            QMessageBox.information(
                self,
                "Разметка не требуется",
                "Камеры мультикамерного трекинга следят по всей области кадра и не требуют линий забора."
            )
            return

        cameras = self._get_cameras()
        camera = next((c for c in cameras if c["name"] == camera_name), None)

        if not camera or not camera.get("preview_frame"):
            QMessageBox.warning(self, "Нет видео", "Для настройки линий нужно загрузить тестовое видео в папку камеры.")
            return

        dialog = ZoneEditorDialog(camera_name, camera["preview_frame"], self)
        if dialog.exec():
            self.refresh()
