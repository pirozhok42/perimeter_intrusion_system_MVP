from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox
from app.gui.auth import check_credentials

class LoginWindow(QWidget):
    login_success = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Perimeter Vision - Login")
        self.setMinimumSize(900, 560)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(420)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(16)

        title = QLabel("Perimeter Vision")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Вход в систему видеоконтроля периметра")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин или email")
        self.login_input.setText("admin")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText("admin")

        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self._handle_login)

        skip_btn = QPushButton("Пропустить")
        skip_btn.setObjectName("SecondaryButton")
        skip_btn.clicked.connect(lambda: self.login_success.emit("dev_user"))

        hint = QLabel("Тестовый доступ: admin / admin")
        hint.setObjectName("Subtitle")
        hint.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        layout.addWidget(skip_btn)
        layout.addWidget(hint)

        root.addWidget(card)

    def _handle_login(self):
        login = self.login_input.text()
        password = self.password_input.text()

        if check_credentials(login, password):
            self.login_success.emit(login)
            return

        QMessageBox.warning(self, "Ошибка входа", "Неверный логин или пароль")
