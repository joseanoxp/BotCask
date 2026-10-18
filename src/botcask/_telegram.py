import http.client
import json
import math
import urllib.error
import urllib.request
from collections.abc import Mapping

from ._errors import TelegramAPIError, TelegramTransportError
from ._execution import CommandResult

_TELEGRAM_API_BASE_URL = "https://api.telegram.org"


def build_send_message_payload(
    chat_id: object,
    result: CommandResult,
) -> dict[str, object]:
    if isinstance(chat_id, bool) or not isinstance(chat_id, int | str):
        raise TypeError("chat_id must be a string or integer")
    if isinstance(chat_id, str):
        chat_id = chat_id.strip()
        if not chat_id:
            raise ValueError("chat_id must not be empty")

    payload: dict[str, object] = {
        "chat_id": chat_id,
        "text": result.text,
    }
    if result.reply_markup is not None:
        payload["reply_markup"] = result.reply_markup.model_dump()

    return payload


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_token(token: object) -> str:
    if not isinstance(token, str):
        raise TypeError("token must be a string")
    normalized = token.strip()
    if not normalized:
        raise ValueError("token must not be empty")
    if any(ch.isspace() for ch in normalized) or any(
        ch in normalized for ch in ("/", "?", "#", "\\")
    ):
        raise ValueError("token contains invalid characters")
    return normalized


def _validate_timeout(timeout: object) -> float:
    if isinstance(timeout, bool) or not isinstance(timeout, int | float):
        raise TypeError("timeout must be a positive finite number")
    value = float(timeout)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("timeout must be a positive finite number")
    return value


def _build_api_error(
    envelope: Mapping[str, object],
    token: str,
) -> TelegramAPIError:
    raw_code = envelope.get("error_code")
    error_code = raw_code if _is_int(raw_code) else None

    raw_description = envelope.get("description")
    description = (
        raw_description.strip().replace(token, "<redacted>")
        if isinstance(raw_description, str) and raw_description.strip()
        else "Telegram request failed"
    )

    retry_after: int | None = None
    parameters = envelope.get("parameters")
    if isinstance(parameters, Mapping):
        raw_retry_after = parameters.get("retry_after")
        if _is_int(raw_retry_after):
            retry_after = raw_retry_after

    return TelegramAPIError(
        description,
        error_code=error_code,
        retry_after=retry_after,
    )


def _decode_json_object(
    raw_body: bytes,
    *,
    http_status: int | None = None,
) -> dict[str, object]:
    decoded: object = None
    malformed = False
    try:
        decoded = json.loads(raw_body.decode("utf-8"))
    except UnicodeDecodeError, json.JSONDecodeError:
        malformed = True

    if malformed:
        if http_status is not None:
            raise TelegramTransportError(
                f"Telegram Bot API HTTP {http_status} response was not valid JSON"
            )
        raise TelegramTransportError("Telegram Bot API returned malformed JSON")

    if not isinstance(decoded, dict):
        raise TelegramTransportError("Telegram Bot API response must be a JSON object")
    return decoded


def _read_response(
    request: urllib.request.Request,
    timeout: float,
) -> tuple[bytes, int | None]:
    raw_body = b""
    http_status: int | None = None
    transport_error: str | None = None

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read()
    except urllib.error.HTTPError as exc:
        http_status = exc.code
        try:
            raw_body = exc.read()
        except TimeoutError:
            transport_error = "Telegram Bot API request timed out"
        except urllib.error.URLError, OSError, http.client.HTTPException:
            transport_error = (
                f"Telegram Bot API HTTP {http_status} error body could not be read"
            )
        finally:
            exc.close()
    except TimeoutError:
        transport_error = "Telegram Bot API request timed out"
    except urllib.error.URLError, OSError, http.client.HTTPException:
        transport_error = "Telegram Bot API request failed due to a network error"

    if transport_error is not None:
        raise TelegramTransportError(transport_error)

    return raw_body, http_status


def send_message_request(
    token: str,
    payload: Mapping[str, object],
    *,
    timeout: float = 10.0,
) -> dict[str, object]:
    normalized_token = _validate_token(token)
    normalized_timeout = _validate_timeout(timeout)

    request = urllib.request.Request(
        f"{_TELEGRAM_API_BASE_URL}/bot{normalized_token}/sendMessage",
        data=json.dumps(dict(payload)).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    raw_body, http_status = _read_response(request, normalized_timeout)
    envelope = _decode_json_object(raw_body, http_status=http_status)

    ok = envelope.get("ok")
    if ok is False:
        raise _build_api_error(envelope, normalized_token)
    if http_status is not None:
        raise TelegramTransportError(
            f"Telegram Bot API HTTP {http_status} returned an unexpected response envelope"
        )
    if ok is not True:
        raise TelegramTransportError(
            "Telegram Bot API response is missing boolean 'ok' field"
        )

    result = envelope.get("result")
    if not isinstance(result, dict):
        raise TelegramTransportError(
            "Telegram Bot API success response is missing object 'result' field"
        )
    return result
