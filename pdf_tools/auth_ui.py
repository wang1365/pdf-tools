from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from .authorization import (
    AuthorizationStore,
    get_authorization_status,
    get_device_fingerprint,
    import_offline_license,
    poll_device_binding,
    start_device_binding,
)


def require_authorization(parent: QWidget | None = None) -> bool:
    result = get_authorization_status()
    if result.valid:
        return True
    QMessageBox.warning(parent, "需要授权", f"请先在授权中心绑定在线订阅或导入离线 License。\n\n{result.message}")
    return False


class AuthPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.store = AuthorizationStore()
        self.poll_code: str | None = None
        self.confirm_url: str | None = None
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.on_poll)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        title = QLabel("授权中心")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        lay.addWidget(title)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        lay.addWidget(self.status_label)

        self.device_label = QLabel(f"设备指纹：{get_device_fingerprint()}")
        self.device_label.setWordWrap(True)
        lay.addWidget(self.device_label)

        self.code_label = QLabel("绑定码：-")
        self.code_label.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: 2px;")
        lay.addWidget(self.code_label)

        row = QHBoxLayout()
        self.bind_btn = QPushButton("生成在线绑定码")
        self.open_confirm_btn = QPushButton("打开网页确认")
        self.import_btn = QPushButton("导入离线 License")
        self.refresh_btn = QPushButton("刷新状态")
        row.addWidget(self.bind_btn)
        row.addWidget(self.open_confirm_btn)
        row.addWidget(self.import_btn)
        row.addWidget(self.refresh_btn)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)

        self.open_confirm_btn.setEnabled(False)
        self.bind_btn.clicked.connect(self.on_start_binding)
        self.open_confirm_btn.clicked.connect(self.on_open_confirm)
        self.import_btn.clicked.connect(self.on_import_license)
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.refresh_status()

    def refresh_status(self):
        result = get_authorization_status(self.store)
        prefix = "已授权" if result.valid else "未授权"
        self.status_label.setText(f"{prefix}：{result.message}")

    def on_start_binding(self):
        try:
            data = start_device_binding()
        except Exception as exc:
            QMessageBox.critical(self, "绑定失败", str(exc))
            return

        self.poll_code = str(data["pollCode"])
        self.confirm_url = str(data["confirmUrl"])
        self.code_label.setText(f"绑定码：{data['userCode']}")
        self.open_confirm_btn.setEnabled(True)
        self.timer.start()
        QMessageBox.information(self, "绑定码已生成", "请在网页账户中心确认该设备绑定。")

    def on_open_confirm(self):
        if self.confirm_url:
            from .authorization import DEFAULT_SERVER_URL

            QDesktopServices.openUrl(QUrl(f"{DEFAULT_SERVER_URL}{self.confirm_url}"))

    def on_poll(self):
        if not self.poll_code:
            self.timer.stop()
            return
        try:
            data = poll_device_binding(self.poll_code, self.store)
        except Exception as exc:
            self.timer.stop()
            QMessageBox.warning(self, "绑定查询失败", str(exc))
            return

        if data.get("status") == "confirmed":
            self.timer.stop()
            self.poll_code = None
            self.refresh_status()
            QMessageBox.information(self, "绑定成功", "在线订阅绑定成功。")
        elif data.get("status") in {"expired", "revoked"}:
            self.timer.stop()
            QMessageBox.warning(self, "绑定失败", "绑定码已过期，请重新生成。")

    def on_import_license(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择离线 License", "", "License (*.lic *.json)")
        if not file_name:
            return
        result = import_offline_license(Path(file_name), self.store)
        if result.valid:
            self.refresh_status()
            QMessageBox.information(self, "导入成功", result.message)
        else:
            QMessageBox.warning(self, "导入失败", result.message)
