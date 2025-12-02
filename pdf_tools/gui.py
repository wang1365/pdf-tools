from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QSpinBox, QCheckBox, QFileDialog, QProgressBar, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from .converter import convert_pdf_to_docx

class ConvertThread(QThread):
    started_signal = Signal()
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, pdf_path: str, docx_path: str, start_page: int | None, end_page: int | None):
        super().__init__()
        self.pdf_path = pdf_path
        self.docx_path = docx_path
        self.start_page = start_page
        self.end_page = end_page

    def run(self):
        self.started_signal.emit()
        try:
            convert_pdf_to_docx(self.pdf_path, self.docx_path, start=self.start_page, end=self.end_page)
            self.finished_signal.emit(self.docx_path)
        except Exception as e:
            self.error_signal.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF to Word")
        ip = Path(__file__).resolve().parent.parent / "assets" / "icon" / "app.png"
        if ip.exists():
            self.setWindowIcon(QIcon(str(ip)))
        cw = QWidget()
        self.setCentralWidget(cw)
        lay = QVBoxLayout(cw)

        self.input_edit = QLineEdit()
        self.input_btn = QPushButton("选择PDF")
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("输入PDF"))
        r1.addWidget(self.input_edit)
        r1.addWidget(self.input_btn)
        lay.addLayout(r1)

        self.output_edit = QLineEdit()
        self.output_btn = QPushButton("保存为")
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("输出DOCX"))
        r2.addWidget(self.output_edit)
        r2.addWidget(self.output_btn)
        lay.addLayout(r2)

        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(0)
        self.start_spin.setSpecialValueText("")
        self.start_spin.setValue(0)
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(0)
        self.end_spin.setSpecialValueText("")
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("开始页(0基)"))
        r3.addWidget(self.start_spin)
        r3.addWidget(QLabel("结束页(含)"))
        r3.addWidget(self.end_spin)
        lay.addLayout(r3)

        self.overwrite_cb = QCheckBox("覆盖已存在输出")
        lay.addWidget(self.overwrite_cb)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        lay.addWidget(self.progress)

        self.convert_btn = QPushButton("开始转换")
        lay.addWidget(self.convert_btn)

        self.input_btn.clicked.connect(self.on_browse_input)
        self.output_btn.clicked.connect(self.on_browse_output)
        self.convert_btn.clicked.connect(self.on_convert)
        self.thread: ConvertThread | None = None

    def on_browse_input(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF (*.pdf)")
        if f:
            self.input_edit.setText(f)
            p = Path(f)
            self.output_edit.setText(str(p.with_suffix(".docx")))

    def on_browse_output(self):
        f, _ = QFileDialog.getSaveFileName(self, "保存DOCX", self.output_edit.text() or "", "Word (*.docx)")
        if f:
            self.output_edit.setText(f)

    def on_convert(self):
        inp = self.input_edit.text().strip()
        out = self.output_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "提示", "请选择输入PDF")
            return
        p = Path(inp)
        if not p.is_file():
            QMessageBox.warning(self, "提示", "输入文件不存在")
            return
        if not out:
            out = str(p.with_suffix(".docx"))
            self.output_edit.setText(out)
        op = Path(out)
        if op.exists() and not self.overwrite_cb.isChecked():
            r = QMessageBox.question(self, "确认", "输出已存在，是否覆盖？")
            if r != QMessageBox.Yes:
                return
        s = self.start_spin.value()
        e = self.end_spin.value() if self.end_spin.value() != 0 else None
        self.progress.show()
        self.convert_btn.setEnabled(False)
        self.thread = ConvertThread(inp, out, s if s != 0 else None, e)
        self.thread.started_signal.connect(lambda: None)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_finished(self, path: str):
        QMessageBox.information(self, "完成", path)

    def on_error(self, msg: str):
        QMessageBox.critical(self, "错误", msg)

    def on_thread_done(self):
        self.progress.hide()
        self.convert_btn.setEnabled(True)
