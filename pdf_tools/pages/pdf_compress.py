from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PdfCompressPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        t = QLabel("PDF压缩")
        t.setAlignment(Qt.AlignmentFlag.AlignLeft)
        s = QLabel("暂未实现")
        s.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(t)
        lay.addWidget(s)

