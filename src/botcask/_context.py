from collections.abc import Mapping
from typing import Any


def telegram_context(update: Mapping[str, Any]) -> dict[str, Any]:
    """Map a Telegram update into the context consumed by command templates."""
    context: dict[str, Any] = {}

    message = update.get("message")
    callback_query = update.get("callback_query")

    if isinstance(message, Mapping):
        context["message"] = dict(message)
        if isinstance(message.get("from"), Mapping):
            context["user"] = dict(message["from"])
        if isinstance(message.get("chat"), Mapping):
            context["chat"] = dict(message["chat"])

    if isinstance(callback_query, Mapping):
        context["callback_query"] = dict(callback_query)
        if isinstance(callback_query.get("from"), Mapping):
            context["user"] = dict(callback_query["from"])

        callback_message = callback_query.get("message")
        if isinstance(callback_message, Mapping):
            context["message"] = dict(callback_message)
            if isinstance(callback_message.get("chat"), Mapping):
                context["chat"] = dict(callback_message["chat"])

    return context
