DARK_THEME = """
QWidget {
    background-color: #0F172A;
    color: #E5E7EB;
    font-family: Segoe UI, Arial;
    font-size: 14px;
}
QFrame#Card, QFrame#CameraCard {
    background-color: #111827;
    border-radius: 18px;
    border: 1px solid #334155;
}
QFrame#WarningCard, QFrame#CameraCardWarning {
    background-color: #3A2B05;
    border-radius: 18px;
    border: 2px solid #F59E0B;
}
QFrame#AlarmCard, QFrame#CameraCardAlarm {
    background-color: #3F1111;
    border-radius: 18px;
    border: 2px solid #DC2626;
}
QFrame#Sidebar {
    background-color: #111827;
    border-radius: 18px;
    border: 1px solid #334155;
}
QLabel#Title {
    font-size: 28px;
    font-weight: 700;
    color: #F9FAFB;
}
QLabel#SectionTitle {
    font-size: 20px;
    font-weight: 700;
    color: #F9FAFB;
}
QLabel#Subtitle {
    font-size: 14px;
    color: #9CA3AF;
}
QLabel#NoVideo {
    background-color: #000000;
    color: #EF4444;
    font-size: 22px;
    font-weight: 800;
    border-radius: 10px;
}
QLabel#NotificationDot {
    background-color: #DC2626;
    color: #FFFFFF;
    border-radius: 7px;
    min-width: 14px;
    max-width: 14px;
    min-height: 14px;
    max-height: 14px;
}
QLineEdit, QComboBox {
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 10px 12px;
    color: #F9FAFB;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #60A5FA;
}
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1D4ED8; }
QPushButton#SecondaryButton {
    background-color: #374151;
    color: #F9FAFB;
}
QPushButton#SecondaryButton:hover { background-color: #4B5563; }
QPushButton#DangerButton {
    background-color: #DC2626;
    color: #FFFFFF;
    min-width: 44px;
    max-width: 44px;
}
QPushButton#DangerButton:hover { background-color: #B91C1C; }
QPushButton#StartButton { background-color: #16A34A; }
QPushButton#StartButton:hover { background-color: #15803D; }
QPushButton#PauseButton { background-color: #F59E0B; color: #111827; }
QPushButton#PauseButton:hover { background-color: #D97706; }
QPushButton#AvatarMenuButton {
    background-color: #1F2937;
    color: #F9FAFB;
    border: 1px solid #475569;
    border-radius: 19px;
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    font-weight: 700;
}
QPushButton#SidebarButton {
    text-align: left;
    padding: 10px 14px;
    border-radius: 10px;
    background-color: transparent;
    color: #E5E7EB;
}
QPushButton#SidebarButton:hover { background-color: #1F2937; }
QPushButton#SidebarButtonAlert {
    text-align: left;
    padding: 10px 14px;
    border-radius: 10px;
    background-color: #3F1111;
    color: #FCA5A5;
}
QPushButton#AddButton {
    font-size: 22px;
    font-weight: 700;
    border-radius: 10px;
}
QMenu {
    background-color: #111827;
    color: #F9FAFB;
    border: 1px solid #374151;
    padding: 6px;
}
QMenu::item { padding: 8px 28px 8px 12px; }
QMenu::item:selected { background-color: #1E3A8A; }
"""
