from pydantic import BaseModel, ConfigDict


class MessageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str


class CommandSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    message: MessageSpec
