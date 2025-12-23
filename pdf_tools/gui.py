from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QWidget

from .pages.pdf_compress import PdfCompressPage
from .pages.pdf_encrypt import PdfEncryptPage
from .pages.pdf_merge import PdfMergePage
from .pages.pdf_split import PdfSplitPage
from .pages.pdf_to_excel import PdfToExcelPage
from .pages.pdf_to_image import PdfToImagePage
from .pages.pdf_to_ppt import PdfToPptPage
from .pages.pdf_to_word import PdfToWordPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tools")

        screen = QApplication.primaryScreen()
        if screen:
            size = screen.availableGeometry().size()
            self.resize(size.width() // 2, size.height() // 2)

        ip = Path(__file__).resolve().parent.parent / "assets" / "icon" / "app.png"
        if ip.exists():
            self.setWindowIcon(QIcon(str(ip)))

        cw = QWidget()
        self.setCentralWidget(cw)

        lay = QHBoxLayout(cw)
        lay.setSpacing(12)
        lay.setContentsMargins(12, 12, 12, 12)

        self.nav = QListWidget()
        self.nav.setFixedWidth(180)
        self.nav.setFrameShape(QFrame.Shape.StyledPanel)
        self.nav.setSpacing(6)

        self.stack = QStackedWidget()
        self.stack.setFrameShape(QFrame.Shape.NoFrame)

        self.pages = [
            ("PDF合并", PdfMergePage()),
            ("PDF分割", PdfSplitPage()),
            ("PDF压缩", PdfCompressPage()),
            ("PDF转WORD", PdfToWordPage()),
            ("PDF转PPT", PdfToPptPage()),
            ("PDF转Excel", PdfToExcelPage()),
            ("PDF转图片", PdfToImagePage()),
            ("PDF加密", PdfEncryptPage()),
        ]

        for title, page in self.pages:
            self.nav.addItem(QListWidgetItem(title))
            self.stack.addWidget(page)

        lay.addWidget(self.nav)
        lay.addWidget(self.stack, 1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(3)
