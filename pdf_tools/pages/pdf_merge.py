from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget


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

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        title = QLabel("PDF合并")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(title)

        self.list_widget = QListWidget()
        lay.addWidget(self.list_widget, 1)

        r_btn = QHBoxLayout()
        self.add_btn = QPushButton("添加PDF")
        self.remove_btn = QPushButton("移除")
        self.up_btn = QPushButton("上移")
        self.down_btn = QPushButton("下移")
        r_btn.addWidget(self.add_btn)
        r_btn.addWidget(self.remove_btn)
        r_btn.addWidget(self.up_btn)
        r_btn.addWidget(self.down_btn)
        r_btn.addStretch(1)
        lay.addLayout(r_btn)

        r_out = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("输出PDF路径")
        self.output_btn = QPushButton("选择输出文件")
        r_out.addWidget(QLabel("输出"))
        r_out.addWidget(self.output_edit, 1)
        r_out.addWidget(self.output_btn)
        lay.addLayout(r_out)

        r_open = QHBoxLayout()
        self.open_btn = QPushButton("打开文件")
        self.open_btn.setEnabled(False)
        r_open.addStretch(1)
        r_open.addWidget(self.open_btn)
        lay.addLayout(r_open)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.merge_btn = QPushButton("开始合并")
        lay.addWidget(self.merge_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.add_btn.clicked.connect(self.on_add)
        self.remove_btn.clicked.connect(self.on_remove)
        self.up_btn.clicked.connect(self.on_up)
        self.down_btn.clicked.connect(self.on_down)
        self.output_btn.clicked.connect(self.on_choose_output)
        self.open_btn.clicked.connect(self.on_open)
        self.merge_btn.clicked.connect(self.on_merge)

    def on_add(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", "", "PDF (*.pdf)")
        for f in files:
            if f:
                item = QListWidgetItem(Path(f).name)
                item.setData(Qt.ItemDataRole.UserRole, f)
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

    def on_merge(self):
        inputs: list[str] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            inputs.append(str(item.data(Qt.ItemDataRole.UserRole)))
        if len(inputs) < 2:
            QMessageBox.warning(self, "提示", "请至少添加2个PDF文件")
            return
        out = self.output_edit.text().strip()
        if not out:
            QMessageBox.warning(self, "提示", "请选择输出文件")
            return

        self.progress.show()
        self.merge_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.thread = MergeThread(inputs, out)
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
        self.merge_btn.setEnabled(True)
