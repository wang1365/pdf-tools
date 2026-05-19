from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .authorization import (
    AuthorizationStore,
    get_authorization_status,
    get_device_fingerprint,
    import_offline_license,
    poll_device_binding,
    save_offline_device_request,
    start_device_binding,
)


def require_authorization(parent: QWidget | None = None) -> bool:
    result = get_authorization_status()
    if result.valid:
        return True
    QMessageBox.warning(
        parent,
        "需要授权",
        f"请先完成任一授权方式：在线登录拉取订阅，或导入离线订阅 License。\n\n{result.message}",
    )
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

        device_row = QHBoxLayout()
        self.copy_device_btn = QPushButton("复制设备指纹")
        self.export_request_btn = QPushButton("导出离线设备请求")
        device_row.addWidget(self.copy_device_btn)
        device_row.addWidget(self.export_request_btn)
        device_row.addStretch(1)
        lay.addLayout(device_row)

        online_box = QGroupBox("方式一：在线登录")
        online_layout = QVBoxLayout(online_box)
        online_note = QLabel("使用个人账号登录官网确认设备后，客户端会自动拉取该账号下的有效订阅和权益。")
        online_note.setWordWrap(True)
        online_layout.addWidget(online_note)

        self.code_label = QLabel("绑定码：-")
        self.code_label.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: 2px;")
        online_layout.addWidget(self.code_label)

        online_row = QHBoxLayout()
        self.bind_btn = QPushButton("生成在线登录绑定码")
        self.open_confirm_btn = QPushButton("打开网页确认")
        online_row.addWidget(self.bind_btn)
        online_row.addWidget(self.open_confirm_btn)
        online_row.addStretch(1)
        online_layout.addLayout(online_row)
        lay.addWidget(online_box)

        offline_box = QGroupBox("方式二：离线订阅 License")
        offline_layout = QVBoxLayout(offline_box)
        offline_note = QLabel("在官网账号中心用本机设备指纹签发离线 License，然后在这里导入 .lic 或 .json 文件。")
        offline_note.setWordWrap(True)
        offline_layout.addWidget(offline_note)

        offline_row = QHBoxLayout()
        self.import_btn = QPushButton("导入离线订阅 License")
        self.refresh_btn = QPushButton("刷新状态")
        offline_row.addWidget(self.import_btn)
        offline_row.addWidget(self.refresh_btn)
        offline_row.addStretch(1)
        offline_layout.addLayout(offline_row)
        lay.addWidget(offline_box)
        lay.addStretch(1)

        self.open_confirm_btn.setEnabled(False)
        self.copy_device_btn.clicked.connect(self.on_copy_device_fingerprint)
        self.export_request_btn.clicked.connect(self.on_export_device_request)
        self.bind_btn.clicked.connect(self.on_start_binding)
        self.open_confirm_btn.clicked.connect(self.on_open_confirm)
        self.import_btn.clicked.connect(self.on_import_license)
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.refresh_status()

    def refresh_status(self):
        result = get_authorization_status(self.store)
        mode = {"online": "在线订阅", "offline": "离线 License"}.get(result.source, "未授权")
        prefix = "已授权" if result.valid else "未授权"
        self.status_label.setText(f"{prefix}（{mode}）：{result.message}")

    def on_copy_device_fingerprint(self):
        QApplication.clipboard().setText(get_device_fingerprint())
        QMessageBox.information(self, "已复制", "设备指纹已复制，可粘贴到官网离线 License 签发页面。")

    def on_export_device_request(self):
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

    def on_start_binding(self):
        try:
            data = start_device_binding()
        except Exception as exc:
            QMessageBox.critical(self, "生成绑定码失败", str(exc))
            return

        self.poll_code = str(data["pollCode"])
        self.confirm_url = str(data["confirmUrl"])
        self.code_label.setText(f"绑定码：{data['userCode']}")
        self.open_confirm_btn.setEnabled(True)
        self.timer.start()
        QMessageBox.information(self, "绑定码已生成", "请在网页登录个人账号，并确认本机设备。确认后客户端会自动拉取订阅。")

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
            QMessageBox.warning(self, "查询绑定状态失败", str(exc))
            return

        if data.get("status") == "confirmed":
            self.timer.stop()
            self.poll_code = None
            self.refresh_status()
            QMessageBox.information(self, "在线登录成功", "已绑定个人账号，并拉取该账号的订阅状态。")
        elif data.get("status") in {"expired", "revoked"}:
            self.timer.stop()
            QMessageBox.warning(self, "绑定失败", "绑定码已过期或已撤销，请重新生成。")

    def on_import_license(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择离线订阅 License", "", "License (*.lic *.json)")
        if not file_name:
            return
        result = import_offline_license(Path(file_name), self.store)
        if result.valid:
            self.refresh_status()
            QMessageBox.information(self, "导入成功", result.message)
        else:
            QMessageBox.warning(self, "导入失败", result.message)
