from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from vinichannels.application.ports.data_provider import ProviderError
from vinichannels.domain.syncing.policies import SyncErrorKind

Json = dict[str, Any]


def as_obj(value: Any) -> Json:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def as_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(0, int(float(value)))
        except ValueError:
            return 0
    return 0


def from_unix(value: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(value), UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


async def send(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    body: Json | None = None,
) -> httpx.Response:
    try:
        return await client.request(method, url, headers=headers, params=params, json=body)
    except httpx.TimeoutException as error:
        raise ProviderError(SyncErrorKind.NETWORK, "Hết thời gian chờ nguồn dữ liệu") from error
    except httpx.HTTPError as error:
        raise ProviderError(SyncErrorKind.NETWORK, "Không kết nối được nguồn dữ liệu") from error


def read_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError as error:
        raise ProviderError(
            SyncErrorKind.SERVER_ERROR, "Nguồn trả về dữ liệu không hợp lệ"
        ) from error


def check_status(
    response: httpx.Response,
    on_auth: Callable[[str], Exception],
    missing_is_channel: bool = True,
    on_missing: Callable[[str], Exception] | None = None,
) -> None:
    status = response.status_code
    if status < 400:
        return
    if status in {401, 402, 403}:
        raise on_auth(f"Nguồn từ chối yêu cầu (mã {status}), kiểm tra khóa hoặc hạn mức")
    if status == 404:
        if missing_is_channel:
            raise ProviderError(SyncErrorKind.NOT_FOUND, "Không tìm thấy kênh trên nguồn này")
        raise (on_missing or on_auth)("Không tìm thấy endpoint hoặc actor của nguồn")
    if status == 429:
        raise ProviderError(SyncErrorKind.RATE_LIMITED, "Nguồn đang giới hạn tần suất gọi")
    raise ProviderError(SyncErrorKind.SERVER_ERROR, f"Nguồn trả về mã {status}")
