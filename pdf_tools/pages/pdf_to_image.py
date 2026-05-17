import io
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QRadioButton, QSpinBox, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..ui_components import ActionRow, DropArea, PathSelectorRow, Section, create_page_header


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
                    out = out_dir / f"{Path(self.pdf_path).stem}_page{i + 1:03d}.{self.fmt}"
                    if self.fmt == "png":
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
                raise RuntimeError("PDF 没有可转换页面")

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addWidget(create_page_header("PDF 转图片", "将 PDF 页面导出为图片，支持逐页导出或合并成长图。"))

        input_section = Section("输入文件")
        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        input_section.body.addWidget(self.drop_area)
        layout.addWidget(input_section)

        param_section = Section("转换参数")
        format_row = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg", "jpeg"])
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setMinimum(72)
        self.dpi_spin.setMaximum(600)
        self.dpi_spin.setValue(150)
        format_row.addWidget(QLabel("格式"))
        format_row.addWidget(self.format_combo)
        format_row.addWidget(QLabel("DPI"))
        format_row.addWidget(self.dpi_spin)
        format_row.addStretch(1)
        param_section.body.addLayout(format_row)

        mode_row = QHBoxLayout()
        self.mode_pages = QRadioButton("每页一张")
        self.mode_single = QRadioButton("合并为一张")
        self.mode_pages.setChecked(True)
        mode_row.addWidget(QLabel("输出模式"))
        mode_row.addWidget(self.mode_pages)
        mode_row.addWidget(self.mode_single)
        mode_row.addStretch(1)
        param_section.body.addLayout(mode_row)

        name_row = QHBoxLayout()
        self.single_name_edit = QLineEdit()
        self.single_name_edit.setPlaceholderText("合并为一张时的输出文件名，可选")
        name_row.addWidget(QLabel("文件名"))
        name_row.addWidget(self.single_name_edit, 1)
        param_section.body.addLayout(name_row)
        layout.addWidget(param_section)

        output_section = Section("输出位置")
        self.out_dir_row = PathSelectorRow("输出文件夹", "选择文件夹", "打开输出", "输出文件夹")
        self.out_dir_edit = self.out_dir_row.edit
        self.out_dir_btn = self.out_dir_row.choose_btn
        self.open_btn = self.out_dir_row.open_btn
        output_section.body.addWidget(self.out_dir_row)
        layout.addWidget(output_section)

        self.action_row = ActionRow("开始转换")
        self.progress = self.action_row.progress
        self.convert_btn = self.action_row.button
        layout.addWidget(self.action_row)
        layout.addStretch(1)

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
        directory = QFileDialog.getExistingDirectory(self, "选择输出文件夹", start_dir)
        if directory:
            self.out_dir_edit.setText(directory)

    def on_open(self):
        if not self.last_output:
            return
        path = Path(self.last_output)
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            QMessageBox.warning(self, "提示", "输出不存在")

    def on_convert(self):
        if not require_authorization(self):
            return
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入 PDF")
            return
        out_dir = self.out_dir_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "提示", "请选择输出文件夹")
            return

        mode = "pages" if self.mode_pages.isChecked() else "single"
        self.action_row.set_processing("正在转换为图片...")
        self.open_btn.setEnabled(False)
        self.thread = PdfToImageThread(
            str(inp),
            out_dir,
            self.format_combo.currentText().strip().lower(),
            int(self.dpi_spin.value()),
            mode,
            self.single_name_edit.text().strip(),
        )
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, out: str):
        self.last_output = out
        self.open_btn.setEnabled(True)
        self.action_row.set_success(f"处理完成：{out}")
        QMessageBox.information(self, "完成", out)

    def on_error(self, msg: str):
        self.action_row.set_error(msg)
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.convert_btn.setEnabled(True)
