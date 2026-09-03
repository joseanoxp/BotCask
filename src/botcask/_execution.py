from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined, UndefinedError
from pydantic import ValidationError

from ._contracts import CommandSpec
from ._errors import (
    CommandNotFoundError,
    CommandRenderError,
    InvalidCommandError,
)


@dataclass(frozen=True, slots=True)
class CommandAction:
    label: str
    command: str


@dataclass(frozen=True, slots=True)
class CommandResult:
    text: str
    actions: tuple[CommandAction, ...] = ()


def execute_command(
    path: str | Path, *, context: dict[str, Any] | None = None
) -> CommandResult:
    command_path = Path(path).resolve()

    try:
        content = yaml.safe_load(command_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CommandNotFoundError(f"Command file {command_path} not found") from exc
    except yaml.YAMLError as exc:
        raise InvalidCommandError(
            f"Invalid command {command_path}: malformed YAML: {exc}"
        ) from exc

    enviroment = Environment(undefined=StrictUndefined)

    try:
        command = CommandSpec.model_validate(content)
    except ValidationError as exc:
        raise InvalidCommandError(f"Invalid command {command_path}: {exc}") from exc

    template = enviroment.from_string(command.response.text)

    try:
        text = template.render(context or {})
    except UndefinedError as exc:
        raise CommandRenderError(
            f"Failed to render command {command_path}: {exc}"
        ) from exc

    actions = tuple(
        CommandAction(label=action.label, command=action.command)
        for action in command.response.actions
    )

    return CommandResult(text=text, actions=actions)
