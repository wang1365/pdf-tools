import html
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget


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
        name = html.escape(path.name)
        full = html.escape(str(path.absolute()))
        self.setText(f"<div style='line-height:1.7'>{name}<br/>{full}</div>")
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


class CompressThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, out_path: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.out_path = out_path

    def run(self):
        try:
            from pypdf import PdfWriter

            writer = PdfWriter(clone_from=self.pdf_path)
            for page in writer.pages:
                page.compress_content_streams(level=9)
            writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

            out = Path(self.out_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as f:
                writer.write(f)
            self.finished_signal.emit(str(out))
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfCompressPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pdf_path: Path | None = None
        self.thread: CompressThread | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        title = QLabel("PDF压缩")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(title)

        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        lay.addWidget(self.drop_area)

        r_out = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("输出PDF路径")
        self.output_btn = QPushButton("选择输出文件")
        r_out.addWidget(QLabel("输出"))
        r_out.addWidget(self.output_edit, 1)
        r_out.addWidget(self.output_btn)
        lay.addLayout(r_out)

        r_open = QHBoxLayout()
        self.open_btn = QPushButton("打开文件")
        self.open_btn.setEnabled(False)
        r_open.addStretch(1)
        r_open.addWidget(self.open_btn)
        lay.addLayout(r_open)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.compress_btn = QPushButton("开始压缩")
        lay.addWidget(self.compress_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.compress_btn.clicked.connect(self.on_compress)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.output_edit.text().strip():
            self.output_edit.setText(str(path.with_name(path.stem + "_compressed.pdf")))

    def on_choose_output(self):
        suggested = self.output_edit.text().strip()
        f, _ = QFileDialog.getSaveFileName(self, "选择输出PDF", suggested or "", "PDF (*.pdf)")
        if f:
            self.output_edit.setText(f)
            self.open_btn.setEnabled(Path(f).exists())

    def on_open(self):
        p = self.output_edit.text().strip()
        if p and Path(p).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        else:
            QMessageBox.warning(self, "提示", "文件不存在")

    def on_compress(self):
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入PDF")
            return
        out = self.output_edit.text().strip()
        if not out:
            QMessageBox.warning(self, "提示", "请选择输出文件")
            return

        self.progress.show()
        self.compress_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.thread = CompressThread(str(inp), out)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, out: str):
        self.output_edit.setText(out)
        self.open_btn.setEnabled(Path(out).exists())
        QMessageBox.information(self, "完成", out)

    def on_error(self, msg: str):
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.compress_btn.setEnabled(True)
