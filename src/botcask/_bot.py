from pathlib import Path
from typing import Any

from ._execution import CommandResult, execute_command


class Bot:
    def __init__(self, *, commands_dir: str | Path) -> None:
        self.commands_dir = Path(commands_dir)

    def execute(
        self, command_name: str, *, context: dict[str, Any] | None = None
    ) -> CommandResult:
        command_path = self.commands_dir / f"{command_name}.yml"
        return execute_command(command_path, context=context)
