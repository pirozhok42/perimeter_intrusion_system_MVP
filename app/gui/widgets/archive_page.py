from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QComboBox, QPushButton, QCheckBox, QMessageBox
)

from app.gui.services.camera_service import list_cameras
from app.gui.services.event_state_service import load_event_history, delete_history_records


class ArchivePage(QWidget):
    def __init__(self):
        super().__init__()
        self.visible_records = []
        self.checkboxes = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(14)

        title = QLabel("Архив событий")
        title.setObjectName("Title")

        controls = QHBoxLayout()

        self.camera_select = QComboBox()
        self.camera_select.currentTextChanged.connect(self.refresh_events)

        refresh_btn = QPushButton("Обновить архив")
        refresh_btn.clicked.connect(self.refresh)

        select_all_btn = QPushButton("Выбрать всё")
        select_all_btn.setObjectName("SecondaryButton")
        select_all_btn.clicked.connect(self._select_all)

        clear_selection_btn = QPushButton("Снять выбор")
        clear_selection_btn.setObjectName("SecondaryButton")
        clear_selection_btn.clicked.connect(self._clear_selection)

        delete_btn = QPushButton("Удалить выбранные")
        delete_btn.setObjectName("DangerButton")
        delete_btn.setMinimumWidth(150)
        delete_btn.clicked.connect(self._delete_selected)

        controls.addWidget(self.camera_select, 1)
        controls.addWidget(refresh_btn)
        controls.addWidget(select_all_btn)
        controls.addWidget(clear_selection_btn)
        controls.addWidget(delete_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.holder = QWidget()
        self.events_layout = QVBoxLayout(self.holder)
        self.events_layout.setSpacing(8)

        self.scroll.setWidget(self.holder)

        layout.addWidget(title)
        layout.addLayout(controls)
        layout.addWidget(self.scroll)

        root.addWidget(card)
        self.refresh()

    def refresh(self):
        current = self.camera_select.currentText()

        self.camera_select.blockSignals(True)
        self.camera_select.clear()
        self.camera_select.addItem("Все камеры")
        for camera in list_cameras():
            self.camera_select.addItem(camera["name"])

        if current:
            idx = self.camera_select.findText(current)
            if idx >= 0:
                self.camera_select.setCurrentIndex(idx)

        self.camera_select.blockSignals(False)
        self.refresh_events()

    def refresh_events(self):
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.checkboxes = []
        selected = self.camera_select.currentText()
        history = load_event_history()

        records = list(enumerate(history))
        if selected and selected != "Все камеры":
            records = [(idx, e) for idx, e in records if e.get("camera_name") == selected]

        self.visible_records = records

        if not records:
            empty = QLabel("Событий в архиве пока нет.")
            empty.setObjectName("Subtitle")
            self.events_layout.addWidget(empty)
            return

        for original_idx, event in reversed(records):
            self.events_layout.addWidget(self._make_event_box(original_idx, event))

        self.events_layout.addStretch()

    def _make_event_box(self, original_idx, event):
        severity = event.get("severity")
        box = QFrame()
        if severity == "alarm":
            box.setObjectName("AlarmCard")
        elif severity == "warning":
            box.setObjectName("WarningCard")
        else:
            box.setObjectName("CameraCard")

        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        top = QHBoxLayout()

        checkbox = QCheckBox()
        checkbox.setProperty("history_index", original_idx)
        self.checkboxes.append(checkbox)

        title = QLabel(f"{event.get('camera_name', '?')} [{event.get('module', 'detection')}] — {event.get('event_type', '?')}")
        title.setObjectName("SectionTitle")

        top.addWidget(checkbox)
        top.addWidget(title, 1)

        text = QLabel(
            f"Время: {event.get('created_at', '?')}. "
            f"Видео: {event.get('video_path', 'нет данных')}. "
            f"Лог: {event.get('log_path', 'нет данных')}."
        )
        text.setObjectName("Subtitle")
        text.setWordWrap(True)

        layout.addLayout(top)
        layout.addWidget(text)

        return box

    def _select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def _clear_selection(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def _delete_selected(self):
        selected_indices = [
            checkbox.property("history_index")
            for checkbox in self.checkboxes
            if checkbox.isChecked()
        ]

        if not selected_indices:
            QMessageBox.information(self, "Архив", "Выбери хотя бы одну запись для удаления.")
            return

        result = QMessageBox.question(
            self,
            "Удаление архивных записей",
            f"Удалить выбранные записи: {len(selected_indices)}?"
        )

        if result != QMessageBox.Yes:
            return

        delete_history_records(selected_indices)
        self.refresh_events()
