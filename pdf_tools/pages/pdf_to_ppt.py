from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QMessageBox, QSpinBox, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..ui_components import ActionRow, DropArea, PathSelectorRow, Section, create_page_header


class PdfToPptThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, out_path: str, dpi: int):
        super().__init__()
        self.pdf_path = pdf_path
        self.out_path = out_path
        self.dpi = dpi

    def run(self):
        try:
            import fitz
            from pptx import Presentation

            out = Path(self.out_path)
            out.parent.mkdir(parents=True, exist_ok=True)

            doc = fitz.open(self.pdf_path)
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            prs = Presentation()
            blank_layout = prs.slide_layouts[6]
            slide_w = prs.slide_width
            slide_h = prs.slide_height

            with TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                for i in range(doc.page_count):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    png = temp_path / f"page_{i + 1:03d}.png"
                    pix.save(str(png))

                    slide = prs.slides.add_slide(blank_layout)
                    pic = slide.shapes.add_picture(str(png), 0, 0)
                    scale = min(slide_w / pic.width, slide_h / pic.height)
                    new_w = int(pic.width * scale)
                    new_h = int(pic.height * scale)
                    pic.left = int((slide_w - new_w) / 2)
                    pic.top = int((slide_h - new_h) / 2)
                    pic.width = new_w
                    pic.height = new_h

            prs.save(str(out))
            self.finished_signal.emit(str(out))
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfToPptPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pdf_path: Path | None = None
        self.thread: PdfToPptThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addWidget(create_page_header("PDF 转 PPT", "将 PDF 页面转换为 PPTX，每页生成一张幻灯片。"))

        input_section = Section("输入文件")
        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        input_section.body.addWidget(self.drop_area)
        layout.addWidget(input_section)

        param_section = Section("转换参数")
        dpi_row = QHBoxLayout()
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setMinimum(72)
        self.dpi_spin.setMaximum(600)
        self.dpi_spin.setValue(150)
        dpi_row.addWidget(QLabel("DPI"))
        dpi_row.addWidget(self.dpi_spin)
        dpi_row.addStretch(1)
        param_section.body.addLayout(dpi_row)
        layout.addWidget(param_section)

        output_section = Section("输出位置")
        self.output_row = PathSelectorRow("输出", "选择输出文件", "打开文件", "输出 PPTX 路径")
        self.output_edit = self.output_row.edit
        self.output_btn = self.output_row.choose_btn
        self.open_btn = self.output_row.open_btn
        output_section.body.addWidget(self.output_row)
        layout.addWidget(output_section)

        self.action_row = ActionRow("开始转换")
        self.progress = self.action_row.progress
        self.convert_btn = self.action_row.button
        layout.addWidget(self.action_row)
        layout.addStretch(1)

        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.convert_btn.clicked.connect(self.on_convert)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.output_edit.text().strip():
            self.output_edit.setText(str(path.with_suffix(".pptx")))

    def on_choose_output(self):
        suggested = self.output_edit.text().strip()
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出 PPTX", suggested or "", "PowerPoint (*.pptx)")
        if file_name:
            if not file_name.lower().endswith(".pptx"):
                file_name += ".pptx"
            self.output_edit.setText(file_name)
            self.open_btn.setEnabled(Path(file_name).exists())

    def on_open(self):
        path = self.output_edit.text().strip()
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "提示", "文件不存在")

    def on_convert(self):
        if not require_authorization(self):
            return
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入 PDF")
            return
        out = self.output_edit.text().strip()
        if not out:
            QMessageBox.warning(self, "提示", "请选择输出文件")
            return

        self.action_row.set_processing("正在转换为 PPT...")
        self.open_btn.setEnabled(False)
        self.thread = PdfToPptThread(str(inp), out, int(self.dpi_spin.value()))
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, out: str):
        self.output_edit.setText(out)
        self.open_btn.setEnabled(Path(out).exists())
        self.action_row.set_success(f"处理完成：{out}")
        QMessageBox.information(self, "完成", out)

    def on_error(self, msg: str):
        self.action_row.set_error(msg)
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.convert_btn.setEnabled(True)
