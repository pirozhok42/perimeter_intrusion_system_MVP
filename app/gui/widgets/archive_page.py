from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QComboBox, QPushButton
from app.gui.services.camera_service import list_cameras
from app.gui.services.event_state_service import load_event_history

class ArchivePage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32,32,32,32)
        title = QLabel("Архив событий")
        title.setObjectName("Title")
        self.camera_select = QComboBox()
        self.camera_select.currentTextChanged.connect(self.refresh_events)
        refresh = QPushButton("Обновить архив")
        refresh.clicked.connect(self.refresh)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.holder = QWidget()
        self.events_layout = QVBoxLayout(self.holder)
        self.scroll.setWidget(self.holder)
        layout.addWidget(title)
        layout.addWidget(self.camera_select)
        layout.addWidget(refresh)
        layout.addWidget(self.scroll)
        root.addWidget(card)
        self.refresh()

    def refresh(self):
        self.camera_select.blockSignals(True)
        self.camera_select.clear()
        self.camera_select.addItem("Все камеры")
        for c in list_cameras():
            self.camera_select.addItem(c["name"])
        self.camera_select.blockSignals(False)
        self.refresh_events()

    def refresh_events(self):
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        selected = self.camera_select.currentText()
        history = load_event_history()
        if selected and selected != "Все камеры":
            history = [e for e in history if e.get("camera_name") == selected]
        if not history:
            label = QLabel("Событий в архиве пока нет.")
            label.setObjectName("Subtitle")
            self.events_layout.addWidget(label)
            return
        for event in reversed(history):
            self.events_layout.addWidget(self._box(event))
        self.events_layout.addStretch()

    def _box(self, e):
        box = QFrame()
        box.setObjectName("AlarmCard" if e.get("severity")=="alarm" else "WarningCard" if e.get("severity")=="warning" else "CameraCard")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16,16,16,16)
        title = QLabel(f"{e.get('camera_name','?')} — {e.get('event_type','?')}")
        title.setObjectName("SectionTitle")
        text = QLabel(f"Время: {e.get('created_at','?')}. Видео: {e.get('video_path','нет данных')}. Лог: {e.get('log_path','нет данных')}.")
        text.setObjectName("Subtitle")
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)
        return box
