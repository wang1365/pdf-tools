from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .auth_ui import AuthPage, get_authorization_summary
from .authorization import (
    AuthorizationStore,
    get_authorization_status,
    get_device_fingerprint,
    import_offline_license,
    save_offline_device_request,
)
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
        self.auth_store = AuthorizationStore()
        self.auth_dialog: QDialog | None = None

        screen = QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            target_width = min(max(1180, int(available.width() * 0.72)), available.width())
            target_height = min(max(760, int(available.height() * 0.78)), available.height())
            self.resize(target_width, target_height)
            self.setMinimumSize(min(980, target_width), min(640, target_height))

            frame = self.frameGeometry()
            frame.moveCenter(available.center())
            self.move(frame.topLeft())
        else:
            self.resize(1180, 760)
            self.setMinimumSize(980, 640)

        ip = Path(__file__).resolve().parent.parent / "assets" / "icon" / "app.png"
        if ip.exists():
            self.setWindowIcon(QIcon(str(ip)))

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f7f8fa;
            }
            QListWidget {
                background: #ffffff;
                border: 1px solid #d8dee6;
                border-radius: 8px;
                font-size: 14px;
                outline: 0;
                padding: 8px;
            }
            QListWidget::item {
                min-height: 40px;
                padding: 8px 12px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background: #e8f1ff;
                color: #0f3f83;
                font-weight: 700;
            }
            QStackedWidget {
                background: #ffffff;
                border: 1px solid #d8dee6;
                border-radius: 8px;
            }
            """
        )
        self.create_menus()

        cw = QWidget()
        self.setCentralWidget(cw)

        lay = QHBoxLayout(cw)
        lay.setSpacing(20)
        lay.setContentsMargins(20, 20, 20, 20)

        self.nav = QListWidget()
        self.nav.setFixedWidth(220)
        self.nav.setFrameShape(QFrame.Shape.StyledPanel)
        self.nav.setSpacing(8)

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
        self.nav.setCurrentRow(0)

    def create_menus(self):
        file_menu = self.menuBar().addMenu("文件")
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        auth_menu = self.menuBar().addMenu("授权")

        open_auth_action = QAction("授权中心...", self)
        open_auth_action.triggered.connect(self.open_auth_center)
        auth_menu.addAction(open_auth_action)

        check_status_action = QAction("查看授权状态", self)
        check_status_action.triggered.connect(self.show_authorization_status)
        auth_menu.addAction(check_status_action)

        auth_menu.addSeparator()

        import_license_action = QAction("导入离线 License...", self)
        import_license_action.triggered.connect(self.import_offline_license_from_menu)
        auth_menu.addAction(import_license_action)

        export_request_action = QAction("导出离线设备请求...", self)
        export_request_action.triggered.connect(self.export_device_request_from_menu)
        auth_menu.addAction(export_request_action)

        copy_fingerprint_action = QAction("复制设备指纹", self)
        copy_fingerprint_action.triggered.connect(self.copy_device_fingerprint)
        auth_menu.addAction(copy_fingerprint_action)

        auth_menu.addSeparator()

        online_login_action = QAction("在线登录绑定...", self)
        online_login_action.triggered.connect(self.open_auth_center)
        auth_menu.addAction(online_login_action)

        help_menu = self.menuBar().addMenu("帮助")
        about_action = QAction("关于 PDF Tools", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_auth_center(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("授权中心")
        dialog.resize(720, 560)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(AuthPage(dialog))
        self.auth_dialog = dialog
        dialog.exec()

    def show_authorization_status(self):
        result = get_authorization_status(self.auth_store)
        summary = get_authorization_summary(result)
        QMessageBox.information(
            self,
            "授权状态",
            "\n".join(
                [
                    f"状态：{summary['status']}",
                    f"方式：{summary['source']}",
                    f"有效期至：{summary['expires_at']}",
                    f"剩余时间：{summary['remaining']}",
                    f"授权版本：{summary['edition']}",
                    f"授权用户：{summary['user']}",
                    f"说明：{summary['message']}",
                ]
            ),
        )

    def import_offline_license_from_menu(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择离线订阅 License", "", "License (*.lic *.json)")
        if not file_name:
            return
        result = import_offline_license(Path(file_name), self.auth_store)
        if result.valid:
            QMessageBox.information(self, "导入成功", "离线 License 已导入并生效。")
        else:
            QMessageBox.warning(self, "导入失败", result.message)

    def export_device_request_from_menu(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "保存离线设备请求",
            "pdf-tools-device-request.json",
            "JSON (*.json)",
        )
        if not file_name:
            return
        try:
            save_offline_device_request(Path(file_name))
        except OSError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            return
        QMessageBox.information(self, "导出成功", "离线设备请求已保存，可用于官网账号中心签发 License。")

    def copy_device_fingerprint(self):
        QApplication.clipboard().setText(get_device_fingerprint())
        QMessageBox.information(self, "已复制", "设备指纹已复制。")

    def show_about(self):
        QMessageBox.about(
            self,
            "关于 PDF Tools",
            "PDF Tools\n\n授权方式：在线登录拉取订阅，或导入离线订阅 License。",
        )
