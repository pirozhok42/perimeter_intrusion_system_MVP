from pathlib import Path
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox

from app.gui.services.camera_service import save_camera_zones


class DrawingLabel(QLabel):
    def __init__(self, image_path: Path):
        super().__init__()
        self.original_pixmap = QPixmap(str(image_path))
        self.setMinimumSize(800, 500)
        self.setAlignment(Qt.AlignCenter)
        self.fence_points = []
        self.zone_points = []
        self.stage = "fence"
        self.display_rect = QRect()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        point = self._widget_to_image_point(event.pos())
        if point is None:
            return

        if self.stage == "fence":
            if len(self.fence_points) < 2:
                self.fence_points.append(point)
            if len(self.fence_points) == 2:
                self.stage = "zone"
        elif self.stage == "zone":
            if len(self.zone_points) < 4:
                self.zone_points.append(point)

        self.update()

    def _widget_to_image_point(self, pos: QPoint):
        if not self.display_rect.contains(pos):
            return None

        x_ratio = (pos.x() - self.display_rect.x()) / self.display_rect.width()
        y_ratio = (pos.y() - self.display_rect.y()) / self.display_rect.height()

        img_x = int(x_ratio * self.original_pixmap.width())
        img_y = int(y_ratio * self.original_pixmap.height())
        return [img_x, img_y]

    def _image_to_widget_point(self, p):
        x_ratio = p[0] / self.original_pixmap.width()
        y_ratio = p[1] / self.original_pixmap.height()
        return QPoint(
            int(self.display_rect.x() + x_ratio * self.display_rect.width()),
            int(self.display_rect.y() + y_ratio * self.display_rect.height())
        )

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.original_pixmap.isNull():
            return

        painter = QPainter(self)
        scaled = self.original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        self.display_rect = QRect(x, y, scaled.width(), scaled.height())

        painter.drawPixmap(self.display_rect, scaled)

        # sterile zone
        if self.zone_points:
            widget_points = [self._image_to_widget_point(p) for p in self.zone_points]
            painter.setPen(QPen(QColor(255, 220, 0), 3))
            painter.setBrush(QBrush(QColor(255, 220, 0, 70)))
            if len(widget_points) >= 2:
                for i in range(len(widget_points) - 1):
                    painter.drawLine(widget_points[i], widget_points[i+1])
            if len(widget_points) == 4:
                painter.drawPolygon(widget_points)

            painter.setBrush(QBrush(QColor(255, 220, 0)))
            for p in widget_points:
                painter.drawEllipse(p, 5, 5)

        # fence line
        if self.fence_points:
            widget_points = [self._image_to_widget_point(p) for p in self.fence_points]
            painter.setPen(QPen(QColor(239, 68, 68), 4))
            if len(widget_points) == 2:
                painter.drawLine(widget_points[0], widget_points[1])
            painter.setBrush(QBrush(QColor(239, 68, 68)))
            for p in widget_points:
                painter.drawEllipse(p, 6, 6)


class ZoneEditorDialog(QDialog):
    def __init__(self, camera_name: str, image_path: Path, parent=None):
        super().__init__(parent)
        self.camera_name = camera_name
        self.image_path = image_path
        self.setWindowTitle(f"Настройка линий — {camera_name}")
        self.setMinimumSize(950, 700)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        self.hint = QLabel("Этап 1: нарисуйте нижнюю линию забора — поставьте 2 точки")
        self.hint.setObjectName("SectionTitle")
        self.hint.setWordWrap(True)

        self.canvas = DrawingLabel(self.image_path)

        controls = QHBoxLayout()
        undo_btn = QPushButton("Отменить точку")
        reset_btn = QPushButton("Сбросить")
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Закрыть")

        undo_btn.clicked.connect(self._undo_point)
        reset_btn.clicked.connect(self._reset)
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        controls.addWidget(undo_btn)
        controls.addWidget(reset_btn)
        controls.addStretch()
        controls.addWidget(save_btn)
        controls.addWidget(cancel_btn)

        root.addWidget(self.hint)
        root.addWidget(self.canvas, 1)
        root.addLayout(controls)

        self.canvas.update = self._wrap_update(self.canvas.update)

    def _wrap_update(self, original_update):
        def wrapped(*args, **kwargs):
            self._update_hint()
            return original_update(*args, **kwargs)
        return wrapped

    def _update_hint(self):
        if len(self.canvas.fence_points) < 2:
            self.hint.setText(f"Этап 1: нарисуйте нижнюю линию забора — точек: {len(self.canvas.fence_points)}/2")
        else:
            self.hint.setText(f"Этап 2: нарисуйте стерильную зону — точек: {len(self.canvas.zone_points)}/4")

    def _undo_point(self):
        if self.canvas.stage == "zone" and self.canvas.zone_points:
            self.canvas.zone_points.pop()
        elif self.canvas.stage == "zone" and not self.canvas.zone_points:
            self.canvas.stage = "fence"
            if self.canvas.fence_points:
                self.canvas.fence_points.pop()
        elif self.canvas.fence_points:
            self.canvas.fence_points.pop()
        self.canvas.update()

    def _reset(self):
        self.canvas.fence_points = []
        self.canvas.zone_points = []
        self.canvas.stage = "fence"
        self.canvas.update()

    def _save(self):
        if len(self.canvas.fence_points) != 2:
            QMessageBox.warning(self, "Не хватает точек", "Нужно поставить 2 точки забора.")
            return

        if len(self.canvas.zone_points) != 4:
            QMessageBox.warning(self, "Не хватает точек", "Нужно поставить 4 точки стерильной зоны.")
            return

        save_camera_zones(
            camera_name=self.camera_name,
            fence_line=self.canvas.fence_points,
            sterile_zone=self.canvas.zone_points,
        )

        QMessageBox.information(self, "Сохранено", f"Линии для камеры «{self.camera_name}» сохранены.")
        self.accept()
