from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ..auth_ui import require_authorization
from ..ui_components import ActionRow, PathSelectorRow, Section, create_page_header


class MergeThread(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, inputs: list[str], output: str):
        super().__init__()
        self.inputs = inputs
        self.output = output

    def run(self):
        try:
            from pypdf import PdfReader, PdfWriter

            writer = PdfWriter()
            for p in self.inputs:
                reader = PdfReader(p)
                for page in reader.pages:
                    writer.add_page(page)
            out_path = Path(self.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as f:
                writer.write(f)
            self.finished_signal.emit(str(out_path))
        except Exception as e:
            self.error_signal.emit(str(e))


class PdfMergePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread: MergeThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        layout.addWidget(create_page_header("PDF 合并", "按列表顺序合并多个 PDF 文件。"))

        input_section = Section("输入文件")
        self.list_widget = QListWidget()
        input_section.body.addWidget(self.list_widget, 1)

        button_row = QHBoxLayout()
        self.add_btn = QPushButton("添加 PDF")
        self.remove_btn = QPushButton("移除")
        self.up_btn = QPushButton("上移")
        self.down_btn = QPushButton("下移")
        button_row.addWidget(self.add_btn)
        button_row.addWidget(self.remove_btn)
        button_row.addWidget(self.up_btn)
        button_row.addWidget(self.down_btn)
        button_row.addStretch(1)
        input_section.body.addLayout(button_row)
        layout.addWidget(input_section, 1)

        output_section = Section("输出位置")
        self.output_row = PathSelectorRow("输出", "选择输出文件", "打开文件", "输出 PDF 路径")
        self.output_edit = self.output_row.edit
        self.output_btn = self.output_row.choose_btn
        self.open_btn = self.output_row.open_btn
        output_section.body.addWidget(self.output_row)
        layout.addWidget(output_section)

        self.action_row = ActionRow("开始合并")
        self.progress = self.action_row.progress
        self.merge_btn = self.action_row.button
        layout.addWidget(self.action_row)

        self.add_btn.clicked.connect(self.on_add)
        self.remove_btn.clicked.connect(self.on_remove)
        self.up_btn.clicked.connect(self.on_up)
        self.down_btn.clicked.connect(self.on_down)
        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.merge_btn.clicked.connect(self.on_merge)

    def on_add(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择 PDF 文件", "", "PDF (*.pdf)")
        for file_name in files:
            if file_name:
                item = QListWidgetItem(Path(file_name).name)
                item.setData(Qt.ItemDataRole.UserRole, file_name)
                self.list_widget.addItem(item)
        if files and not self.output_edit.text().strip():
            first = Path(files[0])
            self.output_edit.setText(str(first.with_name(first.stem + "_merged.pdf")))

    def on_remove(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def on_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def on_down(self):
        row = self.list_widget.currentRow()
        if 0 <= row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

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

    def on_merge(self):
        if not require_authorization(self):
            return
        inputs: list[str] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            inputs.append(str(item.data(Qt.ItemDataRole.UserRole)))
        if len(inputs) < 2:
            QMessageBox.warning(self, "提示", "请至少添加 2 个 PDF 文件")
            return
        out = self.output_edit.text().strip()
        if not out:
            QMessageBox.warning(self, "提示", "请选择输出文件")
            return

        self.action_row.set_processing("正在合并 PDF...")
        self.open_btn.setEnabled(False)
        self.thread = MergeThread(inputs, out)
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
        self.merge_btn.setEnabled(True)
