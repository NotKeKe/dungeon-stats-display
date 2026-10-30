"""共用的 HTTP client：module-level Session 會保留 keep-alive 連線，避免每個請求重新 handshake。"""
import requests

# (connect timeout, read timeout)
TIMEOUT = (5, 15)

# 只送不帶 cookie 狀態的 GET；連線池由 urllib3 加鎖管理，可跨 thread 共用。
_session = requests.Session()


def get(url: str, params: dict[str, str] | None = None) -> requests.Response:
    """和 requests.get 類似，但共用連線池並套用預設 timeout。"""
    return _session.get(url, params=params, timeout=TIMEOUT)
