import pytest

from botcask import CommandResult, InlineKeyboardButton, InlineKeyboardMarkup
from botcask._telegram import build_send_message_payload


@pytest.mark.parametrize("chat_id", [123456789, -1001234567890, "@botcask"])
def test_builds_text_message_payload(chat_id: int | str) -> None:
    result = CommandResult(text="Hello from BotCask!")

    payload = build_send_message_payload(chat_id, result)

    assert payload == {
        "chat_id": chat_id,
        "text": "Hello from BotCask!",
    }


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
