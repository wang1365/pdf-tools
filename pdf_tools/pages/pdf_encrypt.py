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


class EncryptThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, out_path: str, password: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.out_path = out_path
        self.password = password

    def run(self):
        try:
            from pypdf import PdfReader, PdfWriter

            reader = PdfReader(self.pdf_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.encrypt(self.password, algorithm="AES-256")

            out = Path(self.out_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as f:
                writer.write(f)

            self.finished_signal.emit(str(out))
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfEncryptPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pdf_path: Path | None = None
        self.thread: EncryptThread | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        title = QLabel("PDF加密")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(title)

        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        lay.addWidget(self.drop_area)

        r1 = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        r1.addWidget(QLabel("密码"))
        r1.addWidget(self.password_edit, 1)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("输出PDF路径")
        self.output_btn = QPushButton("选择输出文件")
        r2.addWidget(QLabel("输出"))
        r2.addWidget(self.output_edit, 1)
        r2.addWidget(self.output_btn)
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        self.open_btn = QPushButton("打开文件")
        self.open_btn.setEnabled(False)
        r3.addStretch(1)
        r3.addWidget(self.open_btn)
        lay.addLayout(r3)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.encrypt_btn = QPushButton("开始加密")
        lay.addWidget(self.encrypt_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.encrypt_btn.clicked.connect(self.on_encrypt)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.output_edit.text().strip():
            self.output_edit.setText(str(path.with_name(path.stem + "_encrypted.pdf")))

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

    def on_encrypt(self):
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入PDF")
            return
        pwd = self.password_edit.text()
        if not pwd:
            QMessageBox.warning(self, "提示", "请输入密码")
            return
        out = self.output_edit.text().strip()
        if not out:
            QMessageBox.warning(self, "提示", "请选择输出文件")
            return

        self.progress.show()
        self.encrypt_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.thread = EncryptThread(str(inp), out, pwd)
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
        self.encrypt_btn.setEnabled(True)
