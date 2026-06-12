from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QFrame, QMessageBox, QStackedWidget, QSizePolicy, QComboBox
)

from app.gui.widgets.add_camera_page import AddCameraPage
from app.gui.widgets.camera_list_page import CameraListPage
from app.gui.widgets.summary_page import SummaryPage
from app.gui.widgets.archive_page import ArchivePage
from app.gui.services.live_processor import LiveProcessor
from app.gui.services.event_state_service import get_alert_flags


def user_initials(username: str) -> str:
    username = (username or "user").strip()
    if "_" in username:
        parts = [p for p in username.split("_") if p]
        return "".join(p[0] for p in parts[:2]).lower()
    if "@" in username:
        username = username.split("@")[0]
    return username[:2].lower()


class SidebarButton(QPushButton):
    def __init__(self, full_text: str, short_text: str | None = None):
        super().__init__(full_text)
        self.full_text = full_text
        self.short_text = short_text or full_text
        self.has_alert = False
        self.setObjectName("SidebarButton")
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_compact(self, compact: bool):
        base = self.short_text if compact else self.full_text
        self.setText(("● " + base) if self.has_alert else base)

    def set_alert(self, value: bool):
        self.has_alert = value
        self.setObjectName("SidebarButtonAlert" if value else "SidebarButton")
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QWidget):
    logout_requested = Signal()
    theme_toggle_requested = Signal()

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.sidebar_buttons = []
        self.live_processor = None
        self.compact_sidebar = False
        self.setWindowTitle("Perimeter Vision - Dashboard")
        self.setMinimumSize(1100, 700)
        self._build_ui()

    def _build_ui(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 20, 24, 24)
        self.root.setSpacing(20)

        self._build_header()

        self.stack = QStackedWidget()
        self.start_page = self._build_start_page()
        self.workspace_page = self._build_workspace_page()

        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.workspace_page)

        self.root.addWidget(self.stack)
        self._refresh_alerts()

    def _build_header(self):
        top_bar = QHBoxLayout()

        title_box = QVBoxLayout()
        self.header_title = QLabel("Главное меню")
        self.header_title.setObjectName("Title")
        self.header_title.setToolTip("Вернуться в главное меню")
        self.header_title.mousePressEvent = lambda event: self._go_home()

        subtitle = QLabel("MVP интерфейс системы контроля периметра")
        subtitle.setObjectName("Subtitle")

        title_box.addWidget(self.header_title)
        title_box.addWidget(subtitle)

        top_bar.addLayout(title_box)
        top_bar.addStretch()

        self.menu_button = QPushButton(user_initials(self.username))
        self.menu_button.setObjectName("AvatarMenuButton")
        self.menu_button.setToolTip("Меню пользователя")
        self.menu_button.clicked.connect(self._show_user_menu)

        top_bar.addWidget(self.menu_button)
        self.root.addLayout(top_bar)

    def _build_start_page(self):
        content = QFrame()
        content.setObjectName("Card")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        welcome = QLabel(f"Добро пожаловать, {self.username}")
        welcome.setObjectName("Title")

        text = QLabel("Нажми кнопку ниже, чтобы перейти к рабочей панели системы контроля периметра.")
        text.setObjectName("Subtitle")
        text.setWordWrap(True)

        start_btn = QPushButton("Запустить приложение")
        start_btn.setFixedWidth(240)
        start_btn.clicked.connect(self._start_workspace)

        layout.addWidget(welcome)
        layout.addWidget(text)
        layout.addSpacing(12)
        layout.addWidget(start_btn)
        layout.addStretch()

        return content

    def _build_workspace_page(self):
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(230)
        sidebar.setMaximumWidth(280)

        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.setSpacing(10)

        add_btn = QPushButton("+")
        add_btn.setObjectName("AddButton")
        add_btn.setMinimumHeight(42)
        add_btn.clicked.connect(self._show_add_menu)
        side_layout.addWidget(add_btn)

        self.btn_perimeter = SidebarButton("Камеры периметра", "Камеры пер...")
        self.btn_territory = SidebarButton("Камеры территории", "Камеры тер...")
        self.btn_summary = SidebarButton("Сводка", "Сводка")
        self.btn_archive = SidebarButton("Архив", "Архив")
        self.btn_updates = SidebarButton("Обновления", "Обновл...")

        self.sidebar_buttons = [
            self.btn_perimeter,
            self.btn_territory,
            self.btn_summary,
            self.btn_archive,
            self.btn_updates,
        ]

        self.btn_perimeter.clicked.connect(self._open_perimeter_cameras)
        self.btn_territory.clicked.connect(self._open_territory_cameras)
        self.btn_summary.clicked.connect(self._open_summary)
        self.btn_archive.clicked.connect(self._open_archive)
        self.btn_updates.clicked.connect(lambda: self._set_placeholder_section("Обновления"))

        for btn in self.sidebar_buttons:
            side_layout.addWidget(btn)

        side_layout.addStretch()

        self.content_stack = QStackedWidget()

        self.placeholder_page = self._build_placeholder_page("Обновления")
        self.add_camera_page = AddCameraPage(on_camera_created=self._on_camera_created)
        self.perimeter_page = CameraListPage("perimeter")
        self.territory_page = CameraListPage("territory")
        self.summary_page = SummaryPage()
        self.archive_page = ArchivePage()

        self.content_stack.addWidget(self.placeholder_page)
        self.content_stack.addWidget(self.add_camera_page)
        self.content_stack.addWidget(self.perimeter_page)
        self.content_stack.addWidget(self.territory_page)
        self.content_stack.addWidget(self.summary_page)
        self.content_stack.addWidget(self.archive_page)

        layout.addWidget(sidebar)
        layout.addWidget(self.content_stack, 1)

        control_bar = QHBoxLayout()
        control_bar.addStretch()

        self.processing_mode_select = QComboBox()
        self.processing_mode_select.addItem("2 потока: забор + трекинг", "two_streams")
        self.processing_mode_select.addItem("Поток на каждую камеру", "per_camera")
        self.processing_mode_select.addItem("1 поток", "single_thread")

        self.live_status = QLabel("Обработка live: пауза")
        self.live_status.setObjectName("Subtitle")

        self.start_live_btn = QPushButton("▶ Пуск постоянной live-обработки")
        self.start_live_btn.setObjectName("StartButton")
        self.start_live_btn.clicked.connect(self._start_live_processing)

        self.pause_live_btn = QPushButton("⏸ Пауза")
        self.pause_live_btn.setObjectName("PauseButton")
        self.pause_live_btn.clicked.connect(self._pause_live_processing)
        self.pause_live_btn.setEnabled(False)

        control_bar.addWidget(self.processing_mode_select)
        control_bar.addWidget(self.live_status)
        control_bar.addWidget(self.start_live_btn)
        control_bar.addWidget(self.pause_live_btn)

        outer.addLayout(layout, 1)
        outer.addLayout(control_bar)

        return wrapper

    def _build_placeholder_page(self, title_text: str):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)

        self.section_title = QLabel(title_text)
        self.section_title.setObjectName("Title")

        self.section_text = QLabel(f"Раздел «{title_text}» пока в разработке.")
        self.section_text.setObjectName("Subtitle")
        self.section_text.setWordWrap(True)

        layout.addWidget(self.section_title)
        layout.addWidget(self.section_text)
        layout.addStretch()

        return card

    def _go_home(self):
        self.stack.setCurrentWidget(self.start_page)

    def _start_workspace(self):
        self.stack.setCurrentWidget(self.workspace_page)
        self._open_perimeter_cameras()

    def _show_add_menu(self):
        menu = QMenu(self)
        add_camera = menu.addAction("Добавить камеру")
        add_zone = menu.addAction("Добавить зонирование")

        add_camera.triggered.connect(self._open_add_camera)
        add_zone.triggered.connect(lambda: self._set_placeholder_section("Добавить зонирование"))

        menu.exec(self.cursor().pos())

    def _open_add_camera(self):
        self.content_stack.setCurrentWidget(self.add_camera_page)

    def _open_perimeter_cameras(self):
        self.perimeter_page.refresh()
        self.content_stack.setCurrentWidget(self.perimeter_page)
        self._refresh_alerts()

    def _open_territory_cameras(self):
        self.territory_page.refresh()
        self.content_stack.setCurrentWidget(self.territory_page)

    def _open_summary(self):
        self.summary_page.refresh()
        self.content_stack.setCurrentWidget(self.summary_page)
        self._refresh_alerts()

    def _open_archive(self):
        self.archive_page.refresh()
        self.content_stack.setCurrentWidget(self.archive_page)

    def _set_placeholder_section(self, title: str):
        self.section_title.setText(title)
        self.section_text.setText(f"Раздел «{title}» пока в разработке. Следующим этапом добавим его функционал.")
        self.content_stack.setCurrentWidget(self.placeholder_page)

    def _on_camera_created(self, camera_name: str):
        if camera_name.startswith("per"):
            self._open_perimeter_cameras()
        elif camera_name.startswith("ter") or camera_name.startswith("trk"):
            self._open_territory_cameras()

    def _start_live_processing(self):
        if self.live_processor and self.live_processor.isRunning():
            return

        self.live_status.setText("Обработка live: запущена, ожидание новых видео")
        self.start_live_btn.setEnabled(False)
        self.pause_live_btn.setEnabled(True)

        self.live_processor = LiveProcessor(source="input_stream/live", processing_mode=self.processing_mode_select.currentData())
        self.live_processor.event_detected.connect(self._handle_live_event)
        self.live_processor.processing_finished.connect(self._handle_live_finished)
        self.live_processor.status_message.connect(self.live_status.setText)
        self.live_processor.start()

    def _pause_live_processing(self):
        if self.live_processor and self.live_processor.isRunning():
            self.live_processor.stop()
        self.live_status.setText("Обработка live: пауза")
        self.start_live_btn.setEnabled(True)
        self.pause_live_btn.setEnabled(False)

    def _handle_live_event(self, camera_name: str, event_type: str):
        self._refresh_alerts()
        self.perimeter_page.refresh()
        self.summary_page.refresh()

    def _handle_live_finished(self):
        self.live_status.setText("Обработка live: пауза")
        self.start_live_btn.setEnabled(True)
        self.pause_live_btn.setEnabled(False)
        self._refresh_alerts()
        self.perimeter_page.refresh()
        self.summary_page.refresh()

    def _refresh_alerts(self):
        detection_alert, tracking_alert, summary_alert = get_alert_flags()
        self.btn_perimeter.set_alert(detection_alert)
        self.btn_territory.set_alert(tracking_alert)
        self.btn_summary.set_alert(summary_alert)
        for btn in self.sidebar_buttons:
            btn.set_compact(self.compact_sidebar)

    def _show_user_menu(self):
        menu = QMenu(self)

        profile_action = menu.addAction("Мой профиль")
        theme_action = menu.addAction("Сменить тему")
        logout_action = menu.addAction("Выйти")

        profile_action.triggered.connect(self._show_profile)
        theme_action.triggered.connect(self.theme_toggle_requested.emit)
        logout_action.triggered.connect(self.logout_requested.emit)

        menu.exec(self.cursor().pos())

    def _show_profile(self):
        QMessageBox.information(self, "Мой профиль", f"Пользователь: {self.username}\\nРоль: administrator")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.compact_sidebar = self.width() < 900
        for btn in self.sidebar_buttons:
            btn.set_compact(self.compact_sidebar)
