import sys
from PySide6.QtWidgets import QApplication

from app.gui.styles import LIGHT_THEME, DARK_THEME
from app.gui.login_window import LoginWindow
from app.gui.main_window import MainWindow

class GuiApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.theme = "dark"
        self.login_window = None
        self.main_window = None
        self.apply_theme()
        self.show_login()

    def apply_theme(self):
        self.app.setStyleSheet(DARK_THEME if self.theme == "dark" else LIGHT_THEME)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    def show_login(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.login_window = LoginWindow()
        self.login_window.login_success.connect(self.show_main)
        self.login_window.show()

    def show_main(self, username: str):
        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self.main_window = MainWindow(username=username)
        self.main_window.theme_toggle_requested.connect(self.toggle_theme)
        self.main_window.logout_requested.connect(self.show_login)
        self.main_window.show()

    def run(self):
        sys.exit(self.app.exec())

def main():
    GuiApp().run()

if __name__ == "__main__":
    main()
