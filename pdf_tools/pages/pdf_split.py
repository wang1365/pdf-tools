from pathlib import Path

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QSpinBox, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..ui_components import ActionRow, DropArea, PathSelectorRow, Section, create_page_header


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addWidget(create_page_header("PDF 分割", "按固定页数拆分 PDF，输出到指定文件夹。"))

        input_section = Section("输入文件")
        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        input_section.body.addWidget(self.drop_area)
        layout.addWidget(input_section)

        param_section = Section("分割参数")
        pages_row = QHBoxLayout()
        self.pages_spin = QSpinBox()
        self.pages_spin.setMinimum(1)
        self.pages_spin.setMaximum(10000)
        self.pages_spin.setValue(10)
        pages_row.addWidget(QLabel("每份页数"))
        pages_row.addWidget(self.pages_spin)
        pages_row.addStretch(1)
        param_section.body.addLayout(pages_row)

        name_row = QHBoxLayout()
        self.base_name_edit = QLineEdit()
        self.base_name_edit.setPlaceholderText("输出文件前缀")
        name_row.addWidget(QLabel("文件前缀"))
        name_row.addWidget(self.base_name_edit, 1)
        param_section.body.addLayout(name_row)
        layout.addWidget(param_section)

        output_section = Section("输出位置")
        self.out_dir_row = PathSelectorRow("输出文件夹", "选择文件夹", "打开文件夹", "输出文件夹")
        self.out_dir_edit = self.out_dir_row.edit
        self.out_dir_btn = self.out_dir_row.choose_btn
        self.open_dir_btn = self.out_dir_row.open_btn
        output_section.body.addWidget(self.out_dir_row)
        layout.addWidget(output_section)

        self.action_row = ActionRow("开始分割")
        self.progress = self.action_row.progress
        self.split_btn = self.action_row.button
        layout.addWidget(self.action_row)
        layout.addStretch(1)

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
        directory = QFileDialog.getExistingDirectory(self, "选择输出文件夹", start_dir)
        if directory:
            self.out_dir_edit.setText(directory)

    def on_open_out_dir(self):
        if self.last_out_dir and self.last_out_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_out_dir)))
        else:
            QMessageBox.warning(self, "提示", "文件夹不存在")

    def on_split(self):
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
        base = self.base_name_edit.text().strip() or inp.stem
        pages_per = int(self.pages_spin.value())

        self.action_row.set_processing("正在分割 PDF...")
        self.open_dir_btn.setEnabled(False)
        self.thread = SplitThread(str(inp), out_dir, pages_per, base)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, out_dir: str):
        self.last_out_dir = Path(out_dir)
        self.open_dir_btn.setEnabled(True)
        self.action_row.set_success(f"处理完成：{out_dir}")
        QMessageBox.information(self, "完成", out_dir)

    def on_error(self, msg: str):
        self.action_row.set_error(msg)
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.split_btn.setEnabled(True)
