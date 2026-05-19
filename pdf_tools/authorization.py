from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request

PRODUCT_CODE = "pdf-tools-pro"
REQUIRED_ENTITLEMENT = "desktop_basic_access"
DEFAULT_SERVER_URL = os.environ.get("PDF_TOOLS_SERVER_URL", "http://localhost:3000").rstrip("/")
DEFAULT_LICENSE_PUBLIC_KEY_PEM = "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA4Bx0AX/czvQ/6h0kyK1kP/WTtklrD8UTD5ya3I4wHUE=\n-----END PUBLIC KEY-----\n"
PUBLIC_KEY_PEM = os.environ.get("PDF_TOOLS_LICENSE_PUBLIC_KEY", DEFAULT_LICENSE_PUBLIC_KEY_PEM).replace("\\n", "\n").strip()


@dataclass
class AuthorizationResult:
    valid: bool
    message: str
    source: str = "none"
    payload: dict[str, Any] | None = None


def parse_iso_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def build_canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def is_cache_valid(state: dict[str, Any], now: datetime | None = None) -> bool:
    cache_until = state.get("cacheUntil")
    if not isinstance(cache_until, str):
        return False
    now = now or datetime.now(UTC)
    try:
        return parse_iso_datetime(cache_until) > now
    except ValueError:
        return False


def get_config_dir() -> Path:
    if os.name == "nt":
        root = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(root) / "PDF Tools"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pdf-tools"


class AuthorizationStore:
    def __init__(self, path: Path | None = None):
        self.path = path or get_config_dir() / "authorization.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def get_device_fingerprint() -> str:
    raw = "|".join(
        [
            platform.node(),
            platform.system(),
            platform.machine(),
            str(uuid.getnode()),
        ]
    )
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_device_info() -> dict[str, str]:
    return {
        "deviceFingerprint": get_device_fingerprint(),
        "deviceName": platform.node() or "Unknown Device",
        "osName": platform.system().lower(),
        "osArch": platform.machine(),
        "appVersion": "0.1.0",
    }


def build_offline_device_request(now: datetime | None = None) -> dict[str, Any]:
    device = get_device_info()
    return {
        "schema_version": 1,
        "product": PRODUCT_CODE,
        "device_fingerprint": device["deviceFingerprint"],
        "device_name": device["deviceName"],
        "os_name": device["osName"],
        "os_arch": device["osArch"],
        "app_version": device["appVersion"],
        "created_at": (now or datetime.now(UTC)).isoformat().replace("+00:00", "Z"),
    }


def save_offline_device_request(path: Path) -> None:
    path.write_text(
        build_canonical_json(build_offline_device_request()) + "\n",
        encoding="utf-8",
    )


def verify_offline_license_document(
    document: dict[str, Any],
    *,
    expected_product: str,
    device_fingerprint: str,
    public_key_pem: str,
    now: datetime | None = None,
) -> AuthorizationResult:
    now = now or datetime.now(UTC)
    if "device_fingerprint" in document and "license_id" not in document:
        return AuthorizationResult(False, "这是离线设备请求文件，不是 License。请在网页端签发并下载 .lic 文件后再导入。", "offline")
    if not isinstance(document.get("license_id"), str) or not isinstance(document.get("signature"), str):
        return AuthorizationResult(False, "离线 License 文件不完整，请导入网页端签发下载的 .lic 文件", "offline")
    if document.get("product") != expected_product:
        return AuthorizationResult(False, "License 产品不匹配", "offline")
    if document.get("signature_alg") != "Ed25519":
        return AuthorizationResult(False, "License 签名算法不支持", "offline")
    if document.get("device", {}).get("fingerprint") != device_fingerprint:
        return AuthorizationResult(False, "License 设备指纹不匹配", "offline")
    if REQUIRED_ENTITLEMENT not in document.get("entitlements", []):
        return AuthorizationResult(False, "License 缺少桌面端权益", "offline")

    try:
        not_before = parse_iso_datetime(str(document["not_before"]))
        expires_at = parse_iso_datetime(str(document["expires_at"]))
    except (KeyError, ValueError):
        return AuthorizationResult(False, "License 有效期格式无效", "offline")

    if now < not_before:
        return AuthorizationResult(False, "License 尚未生效", "offline")
    if now >= expires_at:
        return AuthorizationResult(False, "License 已过期", "offline")

    if not public_key_pem:
        return AuthorizationResult(False, "缺少离线 License 公钥", "offline")

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        return AuthorizationResult(False, "缺少 cryptography 依赖，无法验证 License", "offline")

    signature = document.get("signature")
    if not isinstance(signature, str):
        return AuthorizationResult(False, "License 缺少签名", "offline")

    payload = {key: value for key, value in document.items() if key != "signature"}
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(public_key, Ed25519PublicKey):
            return AuthorizationResult(False, "License 公钥类型无效", "offline")
        public_key.verify(base64.b64decode(signature), build_canonical_json(payload).encode("utf-8"))
    except Exception:
        return AuthorizationResult(False, "License 签名验证失败", "offline")

    return AuthorizationResult(True, "离线授权有效", "offline", document)


def verify_saved_offline_license(store: AuthorizationStore | None = None) -> AuthorizationResult:
    state = (store or AuthorizationStore()).load()
    document = state.get("offlineLicense")
    if not isinstance(document, dict):
        return AuthorizationResult(False, "未导入离线 License", "offline")
    return verify_offline_license_document(
        document,
        expected_product=PRODUCT_CODE,
        device_fingerprint=get_device_fingerprint(),
        public_key_pem=PUBLIC_KEY_PEM,
    )


def check_online_subscription(store: AuthorizationStore | None = None, server_url: str = DEFAULT_SERVER_URL) -> AuthorizationResult:
    store = store or AuthorizationStore()
    state = store.load()
    if is_cache_valid(state):
        return AuthorizationResult(True, "在线订阅缓存有效", "online", state)

    token = state.get("token")
    if not isinstance(token, str) or not token:
        return AuthorizationResult(False, "未绑定在线订阅", "online")

    body = json.dumps(get_device_info()).encode("utf-8")
    req = request.Request(
        f"{server_url}/api/desktop/subscription/check",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        return AuthorizationResult(False, f"在线订阅校验失败：{exc}", "online")

    data = result.get("data") if isinstance(result, dict) else None
    if not result.get("success") or not isinstance(data, dict) or not data.get("active"):
        return AuthorizationResult(False, result.get("message", "在线订阅不可用"), "online")

    next_state = {**state, **data, "token": token}
    store.save(next_state)
    return AuthorizationResult(True, "在线订阅有效", "online", next_state)


def start_device_binding(server_url: str = DEFAULT_SERVER_URL) -> dict[str, Any]:
    body = json.dumps(get_device_info()).encode("utf-8")
    req = request.Request(
        f"{server_url}/api/desktop/device-bind/start",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=8) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        raise RuntimeError(result.get("message", "创建设备绑定失败"))
    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("设备绑定响应无效")
    return data


def poll_device_binding(poll_code: str, store: AuthorizationStore | None = None, server_url: str = DEFAULT_SERVER_URL) -> dict[str, Any]:
    store = store or AuthorizationStore()
    payload = {**get_device_info(), "pollCode": poll_code}
    req = request.Request(
        f"{server_url}/api/desktop/device-bind/poll",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=8) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        raise RuntimeError(result.get("message", "查询设备绑定失败"))
    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("设备绑定查询响应无效")
    token = data.get("token")
    if isinstance(token, str) and token:
        state = store.load()
        state["token"] = token
        store.save(state)
    return data


def import_offline_license(path: Path, store: AuthorizationStore | None = None) -> AuthorizationResult:
    store = store or AuthorizationStore()
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return AuthorizationResult(False, f"读取离线 License 失败：{exc}", "offline")
    if not isinstance(document, dict):
        return AuthorizationResult(False, "离线 License 格式无效", "offline")

    result = verify_offline_license_document(
        document,
        expected_product=PRODUCT_CODE,
        device_fingerprint=get_device_fingerprint(),
        public_key_pem=PUBLIC_KEY_PEM,
    )
    if result.valid:
        state = store.load()
        state["offlineLicense"] = document
        store.save(state)
    return result


def get_authorization_status(store: AuthorizationStore | None = None) -> AuthorizationResult:
    store = store or AuthorizationStore()
    online = check_online_subscription(store)
    if online.valid:
        return online
    offline = verify_saved_offline_license(store)
    if offline.valid:
        return offline
    return AuthorizationResult(False, f"{online.message}；{offline.message}")
