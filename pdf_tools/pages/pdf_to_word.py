from pathlib import Path

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..converter import convert_pdf_to_docx
from ..ui_components import ActionRow, DropArea, Section, create_page_header


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

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.addWidget(create_page_header("PDF 转 Word", "将 PDF 转换为 DOCX 文档，可按页码范围导出。"))

        input_section = Section("输入文件")
        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        input_section.body.addWidget(self.drop_area)
        layout.addWidget(input_section)

        output_section = Section("输出位置")
        output_row = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_btn = QPushButton("选择文件夹")
        output_row.addWidget(QLabel("保存文件夹"))
        output_row.addWidget(self.output_dir_edit, 1)
        output_row.addWidget(self.output_dir_btn)
        output_section.body.addLayout(output_row)

        file_row = QHBoxLayout()
        self.filename_edit = QLineEdit()
        file_row.addWidget(QLabel("文件名"))
        file_row.addWidget(self.filename_edit, 1)
        output_section.body.addLayout(file_row)

        full_path_row = QHBoxLayout()
        self.full_path_edit = QLineEdit()
        self.full_path_edit.setReadOnly(True)
        self.open_file_btn = QPushButton("打开文件")
        self.open_file_btn.setEnabled(False)
        full_path_row.addWidget(QLabel("完整路径"))
        full_path_row.addWidget(self.full_path_edit, 1)
        full_path_row.addWidget(self.open_file_btn)
        output_section.body.addLayout(full_path_row)
        layout.addWidget(output_section)

        param_section = Section("转换参数")
        page_row = QHBoxLayout()
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(0)
        self.start_spin.setSpecialValueText("")
        self.start_spin.setValue(0)
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(0)
        self.end_spin.setSpecialValueText("")
        page_row.addWidget(QLabel("开始页（0 基）"))
        page_row.addWidget(self.start_spin)
        page_row.addWidget(QLabel("结束页（包含）"))
        page_row.addWidget(self.end_spin)
        page_row.addStretch(1)
        param_section.body.addLayout(page_row)

        self.overwrite_cb = QCheckBox("覆盖已存在输出")
        param_section.body.addWidget(self.overwrite_cb)
        layout.addWidget(param_section)

        self.action_row = ActionRow("开始转换")
        self.progress = self.action_row.progress
        self.convert_btn = self.action_row.button
        layout.addWidget(self.action_row)
        layout.addStretch(1)

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
        directory = self.output_dir_edit.text().strip()
        filename = self.filename_edit.text().strip()
        if directory and filename:
            full = str(Path(directory) / filename)
            self.full_path_edit.setText(full)
            self.open_file_btn.setEnabled(Path(full).exists())
        else:
            self.full_path_edit.clear()
            self.open_file_btn.setEnabled(False)

    def on_browse_output_dir(self):
        start_dir = self.output_dir_edit.text().strip() or ""
        directory = QFileDialog.getExistingDirectory(self, "选择保存文件夹", start_dir)
        if directory:
            self.user_set_output_dir = True
            self.output_dir_edit.setText(directory)

    def on_open_file(self):
        path = self.full_path_edit.text().strip()
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "提示", "文件不存在")

    def on_convert(self):
        if not require_authorization(self):
            return
        inp = self.current_pdf_path
        out = self.full_path_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "提示", "请选择输入 PDF")
            return
        if not inp.is_file():
            QMessageBox.warning(self, "提示", "输入文件不存在")
            return
        if not out:
            QMessageBox.warning(self, "提示", "无效的输出路径")
            return

        output_path = Path(out)
        if output_path.exists() and not self.overwrite_cb.isChecked():
            reply = QMessageBox.question(self, "确认", "输出文件已存在，是否覆盖？")
            if reply != QMessageBox.Yes:
                return

        start_page = self.start_spin.value()
        end_page = self.end_spin.value() if self.end_spin.value() != 0 else None

        self.action_row.set_processing("正在转换为 Word...")
        self.open_file_btn.setEnabled(False)
        self.thread = ConvertThread(str(inp), out, start_page if start_page != 0 else None, end_page)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, path: str):
        self.update_full_path()
        self.open_file_btn.setEnabled(Path(path).exists())
        self.action_row.set_success(f"处理完成：{path}")
        QMessageBox.information(self, "完成", path)

    def on_error(self, msg: str):
        self.action_row.set_error(msg)
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.convert_btn.setEnabled(True)
