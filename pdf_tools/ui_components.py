from __future__ import annotations

import html
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def format_file_size(size: int) -> str:
    value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


class DropArea(QLabel):
    file_selected = Signal(Path)

    def __init__(self, text: str = "点击或拖拽 PDF 文件到此处", parent=None):
        super().__init__(parent)
        self.empty_text = text
        self.setObjectName("DropArea")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(text)
        self.setAcceptDrops(True)
        self.setMinimumHeight(96)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.set_empty_style()

    def set_empty_style(self):
        self.setStyleSheet(
            """
            QLabel#DropArea {
                border: 1px dashed #9aa8bd;
                border-radius: 8px;
                padding: 18px;
                background-color: #f8fafc;
                color: #475467;
                line-height: 1.6;
            }
            QLabel#DropArea:hover {
                background-color: #f2f6fb;
                border-color: #2f5f9f;
            }
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_name = url.toLocalFile()
            if file_name.lower().endswith(".pdf"):
                self.update_file(Path(file_name))
                break
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_name, _ = QFileDialog.getOpenFileName(self, "选择 PDF 文件", "", "PDF (*.pdf)")
            if file_name:
                self.update_file(Path(file_name))

    def update_file(self, path: Path):
        size_str = format_file_size(path.stat().st_size)
        name = html.escape(path.name)
        full = html.escape(str(path.absolute()))
        self.setText(f"<b>{name}</b> ({size_str})<br/><span style='color:#667085'>{full}</span>")
        self.setStyleSheet(
            """
            QLabel#DropArea {
                border: 1px solid #3b7a57;
                border-radius: 8px;
                padding: 18px;
                background-color: #eff8f2;
                color: #1f5c3a;
                line-height: 1.6;
            }
            """
        )
        self.file_selected.emit(path)


def create_page_header(title: str, description: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 2)
    layout.setSpacing(6)

    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    description_label = QLabel(description)
    description_label.setObjectName("PageDescription")
    description_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(description_label)
    return widget


class Section(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Section")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 14, 16, 16)
        self.body.setSpacing(12)
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("SectionTitle")
            self.body.addWidget(title_label)


class StatusLabel(QLabel):
    def __init__(self, text: str = "等待操作", parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusLabel")
        self.setWordWrap(True)

    def set_info(self, text: str):
        self.setText(text)
        self.setStyleSheet("color: #566175;")

    def set_success(self, text: str):
        self.setText(text)
        self.setStyleSheet("color: #247a4d; font-weight: 600;")

    def set_error(self, text: str):
        self.setText(text)
        self.setStyleSheet("color: #b42318; font-weight: 600;")


class PathSelectorRow(QWidget):
    def __init__(
        self,
        label: str,
        choose_text: str,
        open_text: str = "打开",
        placeholder: str = "",
        parent=None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label = QLabel(label)
        self.edit = QLineEdit()
        self.edit.setReadOnly(True)
        self.edit.setPlaceholderText(placeholder)
        self.choose_btn = QPushButton(choose_text)
        self.open_btn = QPushButton(open_text)
        self.open_btn.setEnabled(False)

        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.choose_btn)
        layout.addWidget(self.open_btn)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, text: str):
        self.edit.setText(text)

    def open_path(self):
        path_text = self.text()
        if path_text and Path(path_text).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(path_text))


class ActionRow(QWidget):
    def __init__(self, button_text: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.status_label = StatusLabel()
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.button = QPushButton(button_text)
        self.button.setObjectName("PrimaryButton")

        layout.addWidget(self.status_label, 1)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.button)

    def set_processing(self, text: str):
        self.status_label.set_info(text)
        self.progress.show()
        self.button.setEnabled(False)

    def set_idle(self, text: str = "等待操作"):
        self.status_label.set_info(text)
        self.progress.hide()
        self.button.setEnabled(True)

    def set_success(self, text: str):
        self.status_label.set_success(text)
        self.progress.hide()
        self.button.setEnabled(True)

    def set_error(self, text: str):
        self.status_label.set_error(text)
        self.progress.hide()
        self.button.setEnabled(True)
