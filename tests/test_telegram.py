import http.client
import io
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from email.message import Message
from typing import Self

import pytest

from botcask import (
    CommandResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    TelegramAPIError,
    TelegramTransportError,
)
from botcask._telegram import build_send_message_payload, send_message_request


@pytest.mark.parametrize("chat_id", [123456789, -1001234567890, "@botcask"])
def test_builds_text_message_payload(chat_id: int | str) -> None:
    result = CommandResult(text="Hello from BotCask!")

    payload = build_send_message_payload(chat_id, result)

    assert payload == {
        "chat_id": chat_id,
        "text": "Hello from BotCask!",
    }


def test_strips_whitespace_from_string_chat_id() -> None:
    result = CommandResult(text="Hello!")

    payload = build_send_message_payload("  @botcask  ", result)

    assert payload["chat_id"] == "@botcask"


def test_builds_inline_keyboard_payload() -> None:
    result = CommandResult(
        text="Choose an option",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Help", callback_data="help"),
                    InlineKeyboardButton(text="Profile", callback_data="profile"),
                ],
                [InlineKeyboardButton(text="About", callback_data="about")],
            ]
        ),
    )

    payload = build_send_message_payload(123456789, result)

    assert payload == {
        "chat_id": 123456789,
        "text": "Choose an option",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "Help", "callback_data": "help"},
                    {"text": "Profile", "callback_data": "profile"},
                ],
                [{"text": "About", "callback_data": "about"}],
            ]
        },
    }


@pytest.mark.parametrize("chat_id", ["", "   "])
def test_rejects_empty_chat_id(chat_id: str) -> None:
    result = CommandResult(text="Hello!")

    with pytest.raises(ValueError, match="chat_id must not be empty"):
        build_send_message_payload(chat_id, result)


@pytest.mark.parametrize("chat_id", [True, None, 1.5, object()])
def test_rejects_invalid_chat_id_type(chat_id: object) -> None:
    result = CommandResult(text="Hello!")

    with pytest.raises(TypeError, match="chat_id must be a string or integer"):
        build_send_message_payload(chat_id, result)


class _FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _FailingStream(io.BytesIO):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self._error = error

    def read(self, size: int | None = -1) -> bytes:
        raise self._error


def _stub_urlopen(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[urllib.request.Request, float], _FakeHTTPResponse],
) -> None:
    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> _FakeHTTPResponse:
        return handler(request, timeout)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)


def _assert_token_not_exposed(error: BaseException, token: str) -> None:
    assert token not in str(error)
    assert token not in repr(error)
    assert error.__cause__ is None
    assert error.__context__ is None


def test_sends_message_request_and_returns_telegram_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def handler(
        request: urllib.request.Request,
        timeout: float,
    ) -> _FakeHTTPResponse:
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["content_type"] = request.get_header("Content-type")
        captured["body"] = json.loads((request.data or b"").decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeHTTPResponse(
            b'{"ok": true, "result": {"message_id": 42, "chat": {"id": 123456789}}}'
        )

    _stub_urlopen(monkeypatch, handler)

    response = send_message_request(
        "123456:ABC-DEF",
        {"chat_id": 123456789, "text": "Hello from BotCask!"},
        timeout=5.0,
    )

    assert response == {"message_id": 42, "chat": {"id": 123456789}}
    assert captured == {
        "url": "https://api.telegram.org/bot123456:ABC-DEF/sendMessage",
        "method": "POST",
        "content_type": "application/json",
        "body": {"chat_id": 123456789, "text": "Hello from BotCask!"},
        "timeout": 5.0,
    }


def test_raises_telegram_api_error_when_response_is_not_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "secret-bot-token-999"
    _stub_urlopen(
        monkeypatch,
        lambda _req, _timeout: _FakeHTTPResponse(
            b'{"ok": false, "error_code": 400, "description": "Bad Request: chat not found"}'
        ),
    )

    with pytest.raises(TelegramAPIError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    error = exc_info.value
    assert error.error_code == 400
    assert error.description == "Bad Request: chat not found"
    assert error.retry_after is None
    assert "400" in str(error)
    assert "Bad Request: chat not found" in str(error)
    _assert_token_not_exposed(error, token)


def test_surfaces_retry_after_on_http_error_without_retrying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "secret-bot-token-429"
    calls = 0

    def handler(
        request: urllib.request.Request,
        _timeout: float,
    ) -> _FakeHTTPResponse:
        nonlocal calls
        calls += 1
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=429,
            msg="Too Many Requests",
            hdrs=Message(),
            fp=io.BytesIO(
                b'{"ok": false, "error_code": 429, '
                b'"description": "Too Many Requests: retry after 30", '
                b'"parameters": {"retry_after": 30}}'
            ),
        )

    _stub_urlopen(monkeypatch, handler)

    with pytest.raises(TelegramAPIError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    error = exc_info.value
    assert calls == 1
    assert error.error_code == 429
    assert error.description == "Too Many Requests: retry after 30"
    assert error.retry_after == 30
    assert "retry_after=30" in str(error)
    _assert_token_not_exposed(error, token)


@pytest.mark.parametrize(
    "raised_error",
    [
        TimeoutError("request timed out"),
        urllib.error.URLError(
            "connection refused for https://api.telegram.org/botsecret-token-777/sendMessage"
        ),
        http.client.IncompleteRead(b"partial"),
    ],
)
def test_raises_transport_error_on_network_or_timeout_without_leaking_token(
    monkeypatch: pytest.MonkeyPatch,
    raised_error: Exception,
) -> None:
    token = "secret-token-777"

    def handler(
        _request: urllib.request.Request,
        _timeout: float,
    ) -> _FakeHTTPResponse:
        raise raised_error

    _stub_urlopen(monkeypatch, handler)

    with pytest.raises(TelegramTransportError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    _assert_token_not_exposed(exc_info.value, token)


def test_raises_transport_error_when_reading_http_error_body_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "secret-token-read-fail"

    def handler(
        request: urllib.request.Request,
        _timeout: float,
    ) -> _FakeHTTPResponse:
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=502,
            msg="Bad Gateway",
            hdrs=Message(),
            fp=_FailingStream(http.client.IncompleteRead(b"partial")),
        )

    _stub_urlopen(monkeypatch, handler)

    with pytest.raises(TelegramTransportError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    _assert_token_not_exposed(exc_info.value, token)


def test_raises_transport_error_on_non_json_http_error_without_leaking_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "secret-token-502"

    def handler(
        request: urllib.request.Request,
        _timeout: float,
    ) -> _FakeHTTPResponse:
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=502,
            msg="Bad Gateway",
            hdrs=Message(),
            fp=io.BytesIO(b"<html>502 Bad Gateway</html>"),
        )

    _stub_urlopen(monkeypatch, handler)

    with pytest.raises(TelegramTransportError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    assert "502" in str(exc_info.value)
    _assert_token_not_exposed(exc_info.value, token)


@pytest.mark.parametrize(
    "raw_body",
    [
        b"{not-json",
        b"\xff\xfe",
        b"[]",
        b'{"result": {"message_id": 1}}',
        b'{"ok": "true", "result": {"message_id": 1}}',
        b'{"ok": true}',
        b'{"ok": true, "result": ["not-an-object"]}',
    ],
)
def test_raises_transport_error_on_malformed_json_or_unexpected_response_shape(
    monkeypatch: pytest.MonkeyPatch,
    raw_body: bytes,
) -> None:
    token = "secret-token-shape"
    _stub_urlopen(monkeypatch, lambda _req, _timeout: _FakeHTTPResponse(raw_body))

    with pytest.raises(TelegramTransportError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    _assert_token_not_exposed(exc_info.value, token)


def test_redacts_token_when_echoed_in_telegram_error_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "123456:SECRET_TOKEN_XYZ"
    body = json.dumps(
        {
            "ok": False,
            "error_code": 404,
            "description": f"Not Found: /bot{token}/sendMessage",
        }
    ).encode("utf-8")
    _stub_urlopen(monkeypatch, lambda _req, _timeout: _FakeHTTPResponse(body))

    with pytest.raises(TelegramAPIError) as exc_info:
        send_message_request(token, {"chat_id": 123456789, "text": "Hello!"})

    assert token not in exc_info.value.description
    _assert_token_not_exposed(exc_info.value, token)


@pytest.mark.parametrize(
    ("invalid_token", "expected_error"),
    [
        (None, TypeError),
        (12345, TypeError),
        ("", ValueError),
        ("   ", ValueError),
        ("12345:secret/../../other", ValueError),
        ("12345:secret with spaces", ValueError),
    ],
)
def test_rejects_invalid_token_without_exposing_value(
    invalid_token: object,
    expected_error: type[Exception],
) -> None:
    with pytest.raises(expected_error) as exc_info:
        send_message_request(
            invalid_token,  # type: ignore[arg-type]
            {"chat_id": 123456789, "text": "Hello!"},
        )

    if isinstance(invalid_token, str) and invalid_token.strip():
        _assert_token_not_exposed(exc_info.value, invalid_token)


@pytest.mark.parametrize(
    ("invalid_timeout", "expected_error"),
    [
        (True, TypeError),
        ("5", TypeError),
        (0, ValueError),
        (-1.0, ValueError),
        (float("nan"), ValueError),
        (float("inf"), ValueError),
    ],
)
def test_rejects_invalid_timeout(
    invalid_timeout: object,
    expected_error: type[Exception],
) -> None:
    with pytest.raises(expected_error):
        send_message_request(
            "123456:ABC-DEF",
            {"chat_id": 123456789, "text": "Hello!"},
            timeout=invalid_timeout,  # type: ignore[arg-type]
        )
