from pydantic import BaseModel, ConfigDict


class InlineKeyboardButton(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    callback_data: str


class InlineKeyboardMarkup(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    inline_keyboard: list[list[InlineKeyboardButton]]


class MessageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    reply_markup: InlineKeyboardMarkup | None = None


class CommandSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    message: MessageSpec
