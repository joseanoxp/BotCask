from pathlib import Path
from typing import Any

from ._errors import CommandNotFoundError, InvalidCommandError
from ._execution import CommandResult, execute_command


class Bot:
    def __init__(self, *, commands_dir: str | Path = "commands") -> None:
        self.commands_dir = Path(commands_dir).resolve()

    def execute(
        self, command_name: str, *, context: dict[str, Any] | None = None
    ) -> CommandResult:
        if not command_name or command_name in {".", ".."}:
            raise InvalidCommandError("Invalid command name")

        if "/" in command_name or "\\" in command_name:
            raise InvalidCommandError("Invalid command name")

        if command_name.startswith("."):
            raise InvalidCommandError("Invalid command name")

        command_path = (self.commands_dir / f"{command_name}.yml").resolve()
        if command_path.parent != self.commands_dir:
            raise InvalidCommandError("Invalid command name")

        if not command_path.is_file():
            raise CommandNotFoundError(
                f"Command {command_name!r} not found in {self.commands_dir}"
            )

        return execute_command(command_path, context=context)
