import html
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget


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


class SplitThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, out_dir: str, pages_per_part: int, base_name: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.out_dir = out_dir
        self.pages_per_part = pages_per_part
        self.base_name = base_name

    def run(self):
        try:
            from pypdf import PdfReader, PdfWriter

            reader = PdfReader(self.pdf_path)
            total = len(reader.pages)
            out_dir = Path(self.out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            part = 1
            for start in range(0, total, self.pages_per_part):
                writer = PdfWriter()
                for i in range(start, min(start + self.pages_per_part, total)):
                    writer.add_page(reader.pages[i])
                out = out_dir / f"{self.base_name}_part{part:03d}.pdf"
                with out.open("wb") as f:
                    writer.write(f)
                part += 1

            self.finished_signal.emit(str(out_dir))
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfSplitPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pdf_path: Path | None = None
        self.thread: SplitThread | None = None
        self.last_out_dir: Path | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        title = QLabel("PDF分割")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(title)

        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        lay.addWidget(self.drop_area)

        r1 = QHBoxLayout()
        self.pages_spin = QSpinBox()
        self.pages_spin.setMinimum(1)
        self.pages_spin.setMaximum(10000)
        self.pages_spin.setValue(10)
        r1.addWidget(QLabel("每份页数"))
        r1.addWidget(self.pages_spin)
        r1.addStretch(1)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setReadOnly(True)
        self.out_dir_btn = QPushButton("选择文件夹")
        r2.addWidget(QLabel("输出文件夹"))
        r2.addWidget(self.out_dir_edit, 1)
        r2.addWidget(self.out_dir_btn)
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        self.base_name_edit = QLineEdit()
        self.base_name_edit.setPlaceholderText("输出文件前缀")
        r3.addWidget(QLabel("文件前缀"))
        r3.addWidget(self.base_name_edit, 1)
        lay.addLayout(r3)

        r4 = QHBoxLayout()
        self.open_dir_btn = QPushButton("打开文件夹")
        self.open_dir_btn.setEnabled(False)
        r4.addStretch(1)
        r4.addWidget(self.open_dir_btn)
        lay.addLayout(r4)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.split_btn = QPushButton("开始分割")
        lay.addWidget(self.split_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.out_dir_btn.clicked.connect(self.on_choose_out_dir)
        self.open_dir_btn.clicked.connect(self.on_open_out_dir)
        self.split_btn.clicked.connect(self.on_split)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.out_dir_edit.text().strip():
            self.out_dir_edit.setText(str(path.parent))
        if not self.base_name_edit.text().strip():
            self.base_name_edit.setText(path.stem)

    def on_choose_out_dir(self):
        start_dir = self.out_dir_edit.text().strip() or ""
        d = QFileDialog.getExistingDirectory(self, "选择输出文件夹", start_dir)
        if d:
            self.out_dir_edit.setText(d)

    def on_open_out_dir(self):
        if self.last_out_dir and self.last_out_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_out_dir)))
        else:
            QMessageBox.warning(self, "提示", "文件夹不存在")

    def on_split(self):
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入PDF")
            return
        out_dir = self.out_dir_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "提示", "请选择输出文件夹")
            return
        base = self.base_name_edit.text().strip() or inp.stem
        pages_per = int(self.pages_spin.value())

        self.progress.show()
        self.split_btn.setEnabled(False)
        self.open_dir_btn.setEnabled(False)
        self.thread = SplitThread(str(inp), out_dir, pages_per, base)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, out_dir: str):
        self.last_out_dir = Path(out_dir)
        self.open_dir_btn.setEnabled(True)
        QMessageBox.information(self, "完成", out_dir)

    def on_error(self, msg: str):
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.split_btn.setEnabled(True)
