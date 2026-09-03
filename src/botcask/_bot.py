from pathlib import Path
from typing import Any

from ._command_names import is_valid_command_name
from ._errors import InvalidCommandError
from ._execution import CommandResult, execute_command


class Bot:
    def __init__(self, *, commands_dir: str | Path = "commands") -> None:
        self.commands_dir = Path(commands_dir).resolve()

    def execute(
        self, command_name: str, *, context: dict[str, Any] | None = None
    ) -> CommandResult:
        if not is_valid_command_name(command_name):
            raise InvalidCommandError("Invalid command name")

        command_path = (self.commands_dir / f"{command_name}.yml").resolve()
        if command_path.parent != self.commands_dir:
            raise InvalidCommandError("Invalid command name")

        return execute_command(command_path, context=context)
