from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .auth_ui import AuthPage
from .pages.pdf_compress import PdfCompressPage
from .pages.pdf_encrypt import PdfEncryptPage
from .pages.pdf_merge import PdfMergePage
from .pages.pdf_split import PdfSplitPage
from .pages.pdf_to_excel import PdfToExcelPage
from .pages.pdf_to_image import PdfToImagePage
from .pages.pdf_to_ppt import PdfToPptPage
from .pages.pdf_to_word import PdfToWordPage
from .theme import get_app_stylesheet, recommended_window_size


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Tools")
        self.setStyleSheet(get_app_stylesheet())

        screen = QApplication.primaryScreen()
        if screen:
            self.resize(recommended_window_size(screen.availableGeometry().size()))
        else:
            self.resize(recommended_window_size(None))

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon" / "app.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 14, 14, 14)

        sidebar = QFrame()
        sidebar.setStyleSheet("QFrame { background: #172033; border-radius: 8px; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)

        brand = QLabel("PDF Tools")
        brand.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 700; padding: 16px 18px 2px;")
        subtitle = QLabel("本地文档处理工作台")
        subtitle.setStyleSheet("color: #aebbd0; padding: 0 18px 10px;")

        self.nav = QListWidget()
        self.nav.setObjectName("SidebarNav")
        self.nav.setFixedWidth(210)
        self.nav.setFrameShape(QFrame.Shape.NoFrame)
        self.nav.setSpacing(4)

        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addWidget(self.nav, 1)

        workspace = QFrame()
        workspace.setObjectName("WorkspaceFrame")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.setFrameShape(QFrame.Shape.NoFrame)
        workspace_layout.addWidget(self.stack)

        self.pages = [
            ("授权中心", AuthPage()),
            ("PDF 合并", PdfMergePage()),
            ("PDF 分割", PdfSplitPage()),
            ("PDF 压缩", PdfCompressPage()),
            ("PDF 转 Word", PdfToWordPage()),
            ("PDF 转 PPT", PdfToPptPage()),
            ("PDF 转 Excel", PdfToExcelPage()),
            ("PDF 转图片", PdfToImagePage()),
            ("PDF 加密", PdfEncryptPage()),
        ]

        for title, page in self.pages:
            self.nav.addItem(QListWidgetItem(title))
            self.stack.addWidget(page)

        layout.addWidget(sidebar)
        layout.addWidget(workspace, 1)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)
