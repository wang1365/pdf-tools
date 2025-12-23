import html
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget

from ..converter import convert_pdf_to_docx


class DropArea(QLabel):
    file_selected = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("点击或拖拽PDF文件到此处")
        self.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 14px;
                background-color: #f9f9f9;
                color: #555;
                font-size: 14px;
            }
            QLabel:hover {
                background-color: #eef;
                border-color: #88d;
            }
            """
        )
        self.setAcceptDrops(True)
        self.setMinimumHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            f = url.toLocalFile()
            if f.lower().endswith(".pdf"):
                self.update_file(Path(f))
                break
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            f, _ = QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")
            if f:
                self.update_file(Path(f))

    def update_file(self, path: Path):
        size_str = self.format_size(path.stat().st_size)
        name = html.escape(path.name)
        full = html.escape(str(path.absolute()))
        self.setText(f"<div style='line-height:1.7'>{name} ({size_str})<br/>{full}</div>")
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid #4caf50;
                border-radius: 10px;
                padding: 14px;
                background-color: #e8f5e9;
                color: #2e7d32;
                font-size: 14px;
            }
            """
        )
        self.file_selected.emit(path)

    def format_size(self, size: int) -> str:
        value = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024:
                if unit == "B":
                    return f"{int(value)} {unit}"
                return f"{value:.2f} {unit}"
            value /= 1024
        return f"{value:.2f} PB"


class ConvertThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, docx_path: str, start_page: int | None, end_page: int | None):
        super().__init__()
        self.pdf_path = pdf_path
        self.docx_path = docx_path
        self.start_page = start_page
        self.end_page = end_page

    def run(self):
        try:
            convert_pdf_to_docx(self.pdf_path, self.docx_path, start=self.start_page, end=self.end_page)
            self.finished_signal.emit(self.docx_path)
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfToWordPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pdf_path: Path | None = None
        self.user_set_output_dir = False
        self.thread: ConvertThread | None = None

        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(12, 12, 12, 12)

        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        lay.addWidget(self.drop_area)

        r2 = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_btn = QPushButton("选择文件夹")
        r2.addWidget(QLabel("保存文件夹"))
        r2.addWidget(self.output_dir_edit, 1)
        r2.addWidget(self.output_dir_btn)

        self.filename_edit = QLineEdit()
        r2.addWidget(QLabel("文件名"))
        r2.addWidget(self.filename_edit, 1)
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        self.full_path_edit = QLineEdit()
        self.full_path_edit.setReadOnly(True)
        self.open_file_btn = QPushButton("打开文件")
        self.open_file_btn.setEnabled(False)
        r3.addWidget(QLabel("完整路径"))
        r3.addWidget(self.full_path_edit, 1)
        r3.addWidget(self.open_file_btn)
        lay.addLayout(r3)

        r4 = QHBoxLayout()
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(0)
        self.start_spin.setSpecialValueText("")
        self.start_spin.setValue(0)
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(0)
        self.end_spin.setSpecialValueText("")
        r4.addWidget(QLabel("开始页(0基)"))
        r4.addWidget(self.start_spin)
        r4.addWidget(QLabel("结束页(含)"))
        r4.addWidget(self.end_spin)
        lay.addLayout(r4)

        self.overwrite_cb = QCheckBox("覆盖已存在输出")
        lay.addWidget(self.overwrite_cb)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.convert_btn = QPushButton("开始转换")
        lay.addWidget(self.convert_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.output_dir_btn.clicked.connect(self.on_browse_output_dir)
        self.open_file_btn.clicked.connect(self.on_open_file)
        self.convert_btn.clicked.connect(self.on_convert)
        self.output_dir_edit.textChanged.connect(self.update_full_path)
        self.filename_edit.textChanged.connect(self.update_full_path)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        self.filename_edit.setText(path.with_suffix(".docx").name)
        if not self.user_set_output_dir:
            self.output_dir_edit.setText(str(path.parent))
        self.update_full_path()

    def update_full_path(self):
        d = self.output_dir_edit.text().strip()
        f = self.filename_edit.text().strip()
        if d and f:
            full = str(Path(d) / f)
            self.full_path_edit.setText(full)
            self.open_file_btn.setEnabled(Path(full).exists())
        else:
            self.full_path_edit.clear()
            self.open_file_btn.setEnabled(False)

    def on_browse_output_dir(self):
        start_dir = self.output_dir_edit.text().strip() or ""
        d = QFileDialog.getExistingDirectory(self, "选择保存文件夹", start_dir)
        if d:
            self.user_set_output_dir = True
            self.output_dir_edit.setText(d)

    def on_open_file(self):
        p = self.full_path_edit.text().strip()
        if p and Path(p).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        else:
            QMessageBox.warning(self, "提示", "文件不存在")

    def on_convert(self):
        inp = self.current_pdf_path
        out = self.full_path_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "提示", "请选择输入PDF")
            return
        if not inp.is_file():
            QMessageBox.warning(self, "提示", "输入文件不存在")
            return
        if not out:
            QMessageBox.warning(self, "提示", "无效的输出路径")
            return

        op = Path(out)
        if op.exists() and not self.overwrite_cb.isChecked():
            r = QMessageBox.question(self, "确认", "输出已存在，是否覆盖？")
            if r != QMessageBox.Yes:
                return

        s = self.start_spin.value()
        e = self.end_spin.value() if self.end_spin.value() != 0 else None

        self.progress.show()
        self.convert_btn.setEnabled(False)
        self.open_file_btn.setEnabled(False)
        self.thread = ConvertThread(str(inp), out, s if s != 0 else None, e)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, path: str):
        self.update_full_path()
        self.open_file_btn.setEnabled(Path(path).exists())
        QMessageBox.information(self, "完成", path)

    def on_error(self, msg: str):
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.convert_btn.setEnabled(True)

