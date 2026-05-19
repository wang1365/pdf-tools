from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
    AuthorizationResult,
    AuthorizationStore,
    get_authorization_status,
    get_device_fingerprint,
    import_offline_license,
    parse_iso_datetime,
    poll_device_binding,
    save_offline_device_request,
    start_device_binding,
)


def format_local_datetime(value: str | None) -> str:
    if not value:
        return "未提供"
    try:
        return parse_iso_datetime(value).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def format_remaining(value: str | None) -> str:
    if not value:
        return "未知"
    try:
        expires_at = parse_iso_datetime(value)
    except ValueError:
        return "未知"
    seconds = int((expires_at - datetime.now(UTC)).total_seconds())
    if seconds <= 0:
        return "已过期"
    days, remainder = divmod(seconds, 24 * 60 * 60)
    hours = remainder // (60 * 60)
    if days > 0:
        return f"剩余 {days} 天 {hours} 小时"
    minutes = (remainder % (60 * 60)) // 60
    return f"剩余 {hours} 小时 {minutes} 分钟"


def get_authorization_summary(result: AuthorizationResult) -> dict[str, str]:
    payload: dict[str, Any] = result.payload or {}
    source = {"online": "在线订阅", "offline": "离线 License"}.get(result.source, "未授权")
    expires_at = None
    user = "-"
    edition = "-"

    if result.source == "offline":
        expires_at = str(payload.get("expires_at") or "") or None
        edition = str(payload.get("edition") or "-")
        user = str(payload.get("user_id") or "-")
    elif result.source == "online":
        expires_at = str(payload.get("subscriptionExpiresAt") or payload.get("cacheUntil") or "") or None
        edition = str(payload.get("edition") or "-")
        user_payload = payload.get("user")
        if isinstance(user_payload, dict):
            user = str(user_payload.get("nickname") or user_payload.get("id") or "-")

    return {
        "status": "已生效" if result.valid else "未授权",
        "source": source,
        "edition": edition,
        "user": user,
        "expires_at": format_local_datetime(expires_at),
        "remaining": format_remaining(expires_at) if result.valid else "-",
        "message": result.message,
    }


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
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        title = QLabel("授权中心")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("font-size: 22px; font-weight: 800;")
        lay.addWidget(title)

        self.status_card = QGroupBox("")
        self.status_card.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #d6e6d8;
                border-radius: 10px;
                background: #f0f9f1;
                margin-top: 0;
                padding: 12px;
            }
            """
        )
        card_layout = QVBoxLayout(self.status_card)
        card_layout.setSpacing(8)
        self.status_title = QLabel("")
        self.status_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #146c2e;")
        card_layout.addWidget(self.status_title)
        self.status_detail = QLabel("")
        self.status_detail.setWordWrap(True)
        self.status_detail.setStyleSheet("font-size: 13px; line-height: 1.5; color: #1f2937;")
        card_layout.addWidget(self.status_detail)
        lay.addWidget(self.status_card)

        self.device_label = QLabel(f"设备指纹：{get_device_fingerprint()}")
        self.device_label.setWordWrap(True)
        self.device_label.setStyleSheet("color: #4b5563;")
        lay.addWidget(self.device_label)

        offline_box = QGroupBox("方式一：离线订阅 License")
        offline_layout = QVBoxLayout(offline_box)
        offline_note = QLabel("适合无法长期联网的电脑。按下面 3 步完成离线授权：")
        offline_note.setWordWrap(True)
        offline_layout.addWidget(offline_note)

        step_1 = QLabel("1. 导出本机设备请求，得到 pdf-tools-device-request.json。")
        step_1.setWordWrap(True)
        offline_layout.addWidget(step_1)
        step_1_row = QHBoxLayout()
        self.export_request_btn = QPushButton("导出设备请求")
        self.copy_device_btn = QPushButton("复制设备指纹")
        step_1_row.addWidget(self.export_request_btn)
        step_1_row.addWidget(self.copy_device_btn)
        step_1_row.addStretch(1)
        offline_layout.addLayout(step_1_row)

        step_2 = QLabel("2. 登录官网账号中心，导入设备请求并点击“签发并下载 License”。")
        step_2.setWordWrap(True)
        offline_layout.addWidget(step_2)
        step_2_row = QHBoxLayout()
        self.open_offline_page_btn = QPushButton("打开官网离线 License 页面")
        step_2_row.addWidget(self.open_offline_page_btn)
        step_2_row.addStretch(1)
        offline_layout.addLayout(step_2_row)

        step_3 = QLabel("3. 回到这里导入下载得到的 .lic 文件，导入成功后即可使用。")
        step_3.setWordWrap(True)
        offline_layout.addWidget(step_3)
        offline_row = QHBoxLayout()
        self.import_btn = QPushButton("导入已签发 License")
        self.refresh_btn = QPushButton("刷新状态")
        offline_row.addWidget(self.import_btn)
        offline_row.addWidget(self.refresh_btn)
        offline_row.addStretch(1)
        offline_layout.addLayout(offline_row)
        lay.addWidget(offline_box)

        online_box = QGroupBox("方式二：在线登录")
        online_layout = QVBoxLayout(online_box)
        online_note = QLabel("已有网络环境时，可使用个人账号登录官网确认设备，客户端会自动拉取该账号下的有效订阅和权益。")
        online_note.setWordWrap(True)
        online_layout.addWidget(online_note)

        self.code_label = QLabel("绑定码：-")
        self.code_label.setStyleSheet("font-size: 22px; font-weight: 800; letter-spacing: 2px;")
        online_layout.addWidget(self.code_label)

        online_row = QHBoxLayout()
        self.bind_btn = QPushButton("生成在线登录绑定码")
        self.open_confirm_btn = QPushButton("打开网页确认")
        online_row.addWidget(self.bind_btn)
        online_row.addWidget(self.open_confirm_btn)
        online_row.addStretch(1)
        online_layout.addLayout(online_row)
        lay.addWidget(online_box)
        lay.addStretch(1)

        self.open_confirm_btn.setEnabled(False)
        self.copy_device_btn.clicked.connect(self.on_copy_device_fingerprint)
        self.export_request_btn.clicked.connect(self.on_export_device_request)
        self.open_offline_page_btn.clicked.connect(self.on_open_offline_license_page)
        self.bind_btn.clicked.connect(self.on_start_binding)
        self.open_confirm_btn.clicked.connect(self.on_open_confirm)
        self.import_btn.clicked.connect(self.on_import_license)
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.refresh_status()

    def refresh_status(self):
        result = get_authorization_status(self.store)
        summary = get_authorization_summary(result)
        if result.valid:
            self.status_card.setStyleSheet(
                """
                QGroupBox {
                    border: 1px solid #b7e2bd;
                    border-radius: 10px;
                    background: #f0f9f1;
                    margin-top: 0;
                    padding: 12px;
                }
                """
            )
            self.status_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #146c2e;")
        else:
            self.status_card.setStyleSheet(
                """
                QGroupBox {
                    border: 1px solid #f0c5c5;
                    border-radius: 10px;
                    background: #fff5f5;
                    margin-top: 0;
                    padding: 12px;
                }
                """
            )
            self.status_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #b42318;")

        self.status_title.setText(f"{summary['status']} · {summary['source']}")
        self.status_detail.setText(
            "\n".join(
                [
                    f"有效期至：{summary['expires_at']}",
                    f"剩余时间：{summary['remaining']}",
                    f"授权版本：{summary['edition']}",
                    f"授权用户：{summary['user']}",
                    f"状态说明：{summary['message']}",
                ]
            )
        )

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

    def on_open_offline_license_page(self):
        from .authorization import DEFAULT_SERVER_URL

        QDesktopServices.openUrl(QUrl(f"{DEFAULT_SERVER_URL}/account/licenses/offline"))

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
