import html
import io
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton, QRadioButton, QSpinBox, QVBoxLayout, QWidget


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


class PdfToImageThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, out_dir: str, fmt: str, dpi: int, mode: str, single_name: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.out_dir = out_dir
        self.fmt = fmt.lower()
        self.dpi = dpi
        self.mode = mode
        self.single_name = single_name

    def run(self):
        try:
            import fitz
            from PIL import Image

            out_dir = Path(self.out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            doc = fitz.open(self.pdf_path)
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            if self.mode == "pages":
                for i in range(doc.page_count):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    out = out_dir / f"{Path(self.pdf_path).stem}_page{i+1:03d}.{self.fmt}"
                    if self.fmt in {"png"}:
                        pix.save(str(out))
                    else:
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        fmt = "JPEG" if self.fmt in {"jpg", "jpeg"} else self.fmt.upper()
                        img.save(out, format=fmt, quality=95)
                self.finished_signal.emit(str(out_dir))
                return

            images: list[Image.Image] = []
            widths: list[int] = []
            heights: list[int] = []
            for i in range(doc.page_count):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)
                widths.append(img.width)
                heights.append(img.height)

            if not images:
                raise RuntimeError("PDF没有可转换页面")

            max_w = max(widths)
            total_h = sum(heights)
            canvas = Image.new("RGB", (max_w, total_h), (255, 255, 255))
            y = 0
            for img in images:
                x = (max_w - img.width) // 2
                canvas.paste(img, (x, y))
                y += img.height

            name = self.single_name.strip() or f"{Path(self.pdf_path).stem}.{self.fmt}"
            if not name.lower().endswith(f".{self.fmt}"):
                name += f".{self.fmt}"
            out = out_dir / name
            if self.fmt in {"jpg", "jpeg"}:
                canvas.save(out, format="JPEG", quality=95)
            elif self.fmt == "png":
                canvas.save(out, format="PNG")
            else:
                canvas.save(out, format=self.fmt.upper())

            self.finished_signal.emit(str(out))
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfToImagePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pdf_path: Path | None = None
        self.thread: PdfToImageThread | None = None
        self.last_output: str | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        title = QLabel("PDF转图片")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(title)

        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        lay.addWidget(self.drop_area)

        r1 = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg", "jpeg"])
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setMinimum(72)
        self.dpi_spin.setMaximum(600)
        self.dpi_spin.setValue(150)
        r1.addWidget(QLabel("格式"))
        r1.addWidget(self.format_combo)
        r1.addWidget(QLabel("DPI"))
        r1.addWidget(self.dpi_spin)
        r1.addStretch(1)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        self.mode_pages = QRadioButton("每页一张")
        self.mode_single = QRadioButton("合并为一张")
        self.mode_pages.setChecked(True)
        r2.addWidget(QLabel("输出模式"))
        r2.addWidget(self.mode_pages)
        r2.addWidget(self.mode_single)
        r2.addStretch(1)
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setReadOnly(True)
        self.out_dir_btn = QPushButton("选择文件夹")
        r3.addWidget(QLabel("输出文件夹"))
        r3.addWidget(self.out_dir_edit, 1)
        r3.addWidget(self.out_dir_btn)
        lay.addLayout(r3)

        r4 = QHBoxLayout()
        self.single_name_edit = QLineEdit()
        self.single_name_edit.setPlaceholderText("合并为一张时输出文件名(可选)")
        r4.addWidget(QLabel("文件名"))
        r4.addWidget(self.single_name_edit, 1)
        lay.addLayout(r4)

        r5 = QHBoxLayout()
        self.open_btn = QPushButton("打开输出")
        self.open_btn.setEnabled(False)
        r5.addStretch(1)
        r5.addWidget(self.open_btn)
        lay.addLayout(r5)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.convert_btn = QPushButton("开始转换")
        lay.addWidget(self.convert_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.out_dir_btn.clicked.connect(self.on_choose_out_dir)
        self.open_btn.clicked.connect(self.on_open)
        self.convert_btn.clicked.connect(self.on_convert)
        self.mode_pages.toggled.connect(self.on_mode_changed)
        self.on_mode_changed()

    def on_mode_changed(self):
        self.single_name_edit.setEnabled(self.mode_single.isChecked())

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.out_dir_edit.text().strip():
            self.out_dir_edit.setText(str(path.parent))
        if not self.single_name_edit.text().strip():
            self.single_name_edit.setText(path.stem + "." + self.format_combo.currentText())

    def on_choose_out_dir(self):
        start_dir = self.out_dir_edit.text().strip() or ""
        d = QFileDialog.getExistingDirectory(self, "选择输出文件夹", start_dir)
        if d:
            self.out_dir_edit.setText(d)

    def on_open(self):
        if not self.last_output:
            return
        p = Path(self.last_output)
        if p.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
        else:
            QMessageBox.warning(self, "提示", "输出不存在")

    def on_convert(self):
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入PDF")
            return
        out_dir = self.out_dir_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "提示", "请选择输出文件夹")
            return
        fmt = self.format_combo.currentText().strip().lower()
        dpi = int(self.dpi_spin.value())
        mode = "pages" if self.mode_pages.isChecked() else "single"
        single_name = self.single_name_edit.text().strip()

        self.progress.show()
        self.convert_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.thread = PdfToImageThread(str(inp), out_dir, fmt, dpi, mode, single_name)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, out: str):
        self.last_output = out
        self.open_btn.setEnabled(True)
        QMessageBox.information(self, "完成", out)

    def on_error(self, msg: str):
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.convert_btn.setEnabled(True)
