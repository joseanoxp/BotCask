from ._execution import CommandResult


def build_send_message_payload(
    chat_id: object,
    result: CommandResult,
) -> dict[str, object]:
    if isinstance(chat_id, bool) or not isinstance(chat_id, int | str):
        raise TypeError("chat_id must be a string or integer")
    if isinstance(chat_id, str) and not chat_id.strip():
        raise ValueError("chat_id must not be empty")

    payload: dict[str, object] = {
        "chat_id": chat_id,
        "text": result.text,
    }
    if result.reply_markup is not None:
        payload["reply_markup"] = result.reply_markup.model_dump()

    return payload
