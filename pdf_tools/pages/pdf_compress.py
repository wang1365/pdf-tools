from pathlib import Path

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..ui_components import ActionRow, DropArea, PathSelectorRow, Section, create_page_header


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addWidget(create_page_header("PDF 压缩", "压缩 PDF 内容流并去除重复对象，生成更小的 PDF 文件。"))

        input_section = Section("输入文件")
        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        input_section.body.addWidget(self.drop_area)
        layout.addWidget(input_section)

        output_section = Section("输出位置")
        self.output_row = PathSelectorRow("输出", "选择输出文件", "打开文件", "输出 PDF 路径")
        self.output_edit = self.output_row.edit
        self.output_btn = self.output_row.choose_btn
        self.open_btn = self.output_row.open_btn
        output_section.body.addWidget(self.output_row)
        layout.addWidget(output_section)

        self.action_row = ActionRow("开始压缩")
        self.progress = self.action_row.progress
        self.compress_btn = self.action_row.button
        layout.addWidget(self.action_row)
        layout.addStretch(1)

        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.compress_btn.clicked.connect(self.on_compress)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.output_edit.text().strip():
            self.output_edit.setText(str(path.with_name(path.stem + "_compressed.pdf")))

    def on_choose_output(self):
        suggested = self.output_edit.text().strip()
        file_name, _ = QFileDialog.getSaveFileName(self, "选择输出 PDF", suggested or "", "PDF (*.pdf)")
        if file_name:
            self.output_edit.setText(file_name)
            self.open_btn.setEnabled(Path(file_name).exists())

    def on_open(self):
        path = self.output_edit.text().strip()
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "提示", "文件不存在")

    def on_compress(self):
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

        self.action_row.set_processing("正在压缩 PDF...")
        self.open_btn.setEnabled(False)
        self.thread = CompressThread(str(inp), out)
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
        self.compress_btn.setEnabled(True)
