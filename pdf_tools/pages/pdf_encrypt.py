from pathlib import Path

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..ui_components import ActionRow, DropArea, PathSelectorRow, Section, create_page_header


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addWidget(create_page_header("PDF 加密", "为 PDF 设置打开密码，输出 AES-256 加密文件。"))

        input_section = Section("输入文件")
        self.drop_area = DropArea()
        self.drop_area.file_selected.connect(self.on_file_selected)
        input_section.body.addWidget(self.drop_area)
        layout.addWidget(input_section)

        param_section = Section("加密参数")
        password_row = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_row.addWidget(QLabel("密码"))
        password_row.addWidget(self.password_edit, 1)
        param_section.body.addLayout(password_row)
        layout.addWidget(param_section)

        output_section = Section("输出位置")
        self.output_row = PathSelectorRow("输出", "选择输出文件", "打开文件", "输出 PDF 路径")
        self.output_edit = self.output_row.edit
        self.output_btn = self.output_row.choose_btn
        self.open_btn = self.output_row.open_btn
        output_section.body.addWidget(self.output_row)
        layout.addWidget(output_section)

        self.action_row = ActionRow("开始加密")
        self.progress = self.action_row.progress
        self.encrypt_btn = self.action_row.button
        layout.addWidget(self.action_row)
        layout.addStretch(1)

        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.encrypt_btn.clicked.connect(self.on_encrypt)

    def on_file_selected(self, path: Path):
        self.current_pdf_path = path
        if not self.output_edit.text().strip():
            self.output_edit.setText(str(path.with_name(path.stem + "_encrypted.pdf")))

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

    def on_encrypt(self):
        if not require_authorization(self):
            return
        inp = self.current_pdf_path
        if not inp or not inp.is_file():
            QMessageBox.warning(self, "提示", "请选择输入 PDF")
            return
        password = self.password_edit.text()
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            return
        out = self.output_edit.text().strip()
        if not out:
            QMessageBox.warning(self, "提示", "请选择输出文件")
            return

        self.action_row.set_processing("正在加密 PDF...")
        self.open_btn.setEnabled(False)
        self.thread = EncryptThread(str(inp), out, password)
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
        self.encrypt_btn.setEnabled(True)
