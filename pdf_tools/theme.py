from __future__ import annotations

from PySide6.QtCore import QSize


def recommended_window_size(screen_size: QSize | None) -> QSize:
    if screen_size is None:
        return QSize(1180, 760)

    width = min(max(int(screen_size.width() * 0.68), 1080), screen_size.width())
    height = min(max(int(screen_size.height() * 0.72), 720), screen_size.height())
    return QSize(width, height)


def get_app_stylesheet() -> str:
    return """
    QMainWindow {
        background: #eef2f7;
    }
    QWidget {
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 13px;
        color: #172033;
    }
    QListWidget#SidebarNav {
        background: #172033;
        border: none;
        color: #d8e1f0;
        padding: 10px;
        outline: none;
    }
    QListWidget#SidebarNav::item {
        min-height: 38px;
        padding: 8px 12px;
        border-radius: 6px;
    }
    QListWidget#SidebarNav::item:hover {
        background: #23314d;
        color: #ffffff;
    }
    QListWidget#SidebarNav::item:selected {
        background: #2f5f9f;
        color: #ffffff;
        font-weight: 600;
    }
    QFrame#WorkspaceFrame {
        background: #f7f9fc;
        border: 1px solid #dce3ee;
        border-radius: 8px;
    }
    QFrame#Section {
        background: #ffffff;
        border: 1px solid #dce3ee;
        border-radius: 8px;
    }
    QLabel#PageTitle {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
    }
    QLabel#PageDescription {
        color: #667085;
        line-height: 1.5;
    }
    QLabel#SectionTitle {
        font-size: 15px;
        font-weight: 700;
        color: #1f2a44;
    }
    QLabel#StatusLabel {
        color: #566175;
    }
    QLineEdit, QSpinBox, QComboBox {
        min-height: 30px;
        padding: 4px 8px;
        border: 1px solid #cfd8e6;
        border-radius: 5px;
        background: #ffffff;
        selection-background-color: #2f5f9f;
    }
    QLineEdit:read-only {
        background: #f5f7fb;
        color: #475467;
    }
    QPushButton {
        min-height: 30px;
        padding: 5px 14px;
        border: 1px solid #c7d0df;
        border-radius: 5px;
        background: #ffffff;
        color: #263449;
        font-weight: 500;
    }
    QPushButton:hover {
        background: #f3f6fb;
        border-color: #9fb1cb;
    }
    QPushButton:disabled {
        background: #eef1f6;
        color: #98a2b3;
    }
    QPushButton#PrimaryButton {
        background: #1d4f91;
        border-color: #1d4f91;
        color: #ffffff;
        font-weight: 700;
    }
    QPushButton#PrimaryButton:hover {
        background: #17457f;
    }
    QProgressBar {
        min-height: 8px;
        max-height: 8px;
        border: none;
        border-radius: 4px;
        background: #e4e9f2;
    }
    QProgressBar::chunk {
        border-radius: 4px;
        background: #2f5f9f;
    }
    QListWidget {
        background: #ffffff;
        border: 1px solid #dce3ee;
        border-radius: 6px;
        padding: 6px;
    }
    """
