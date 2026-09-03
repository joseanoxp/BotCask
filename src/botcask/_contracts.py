from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._command_names import is_valid_command_name


class ActionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    label: str
    command: str

    @field_validator("command")
    @classmethod
    def command_must_be_a_valid_command_name(cls, value: str) -> str:
        if not is_valid_command_name(value):
            raise ValueError("Invalid command name")
        return value


class ResponseSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    actions: list[ActionSpec] = Field(default_factory=list)


class MessageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str


class CommandSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    response: ResponseSpec | None = None
    message: MessageSpec | None = None

    @model_validator(mode="after")
    def command_must_define_one_output(self) -> Self:
        if (self.response is None) == (self.message is None):
            raise ValueError("Command must define exactly one output")
        return self
