from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined, UndefinedError
from pydantic import ValidationError

from ._contracts import CommandSpec, InlineKeyboardMarkup
from ._errors import (
    CommandNotFoundError,
    CommandRenderError,
    InvalidCommandError,
)


@dataclass(frozen=True, slots=True)
class CommandResult:
    text: str
    reply_markup: InlineKeyboardMarkup | None = None


def _render_value(
    value: object, template_environment: Environment, context: dict[str, Any]
) -> object:
    if isinstance(value, str):
        return template_environment.from_string(value).render(context)
    if isinstance(value, list):
        return [_render_value(item, template_environment, context) for item in value]
    if isinstance(value, dict):
        return {
            key: _render_value(item, template_environment, context)
            for key, item in value.items()
        }
    return value


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

    try:
        rendered_command = CommandSpec.model_validate(
            _render_value(
                command.model_dump(),
                enviroment,
                context or {},
            )
        )
    except UndefinedError as exc:
        raise CommandRenderError(
            f"Failed to render command {command_path}: {exc}"
        ) from exc

    return CommandResult(
        text=rendered_command.message.text,
        reply_markup=rendered_command.message.reply_markup,
    )
