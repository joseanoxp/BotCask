from pathlib import Path

import pytest

from botcask import Bot, CommandNotFoundError, InvalidCommandError


def test_bot_executes_command_discovered_by_name(tmp_path: Path) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    (commands_dir / "start.yml").write_text(
        """
response:
  text: "Hello, {{ user.first_name }}!"
""".strip(),
        encoding="utf-8",
    )

    bot = Bot(commands_dir=commands_dir)

    result = bot.execute("start", context={"user": {"first_name": "Joseano"}})

    assert result.text == "Hello, Joseano!"


def test_bot_executes_separate_commands_by_name(tmp_path: Path) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    (commands_dir / "start.yml").write_text(
        """
response:
  text: "Hello, {{ user.first_name }}!"
""".strip(),
        encoding="utf-8",
    )
    (commands_dir / "help.yml").write_text(
        """
response:
  text: "Available commands: start, help"
""".strip(),
        encoding="utf-8",
    )

    bot = Bot(commands_dir=commands_dir)

    start = bot.execute("start", context={"user": {"first_name": "Joseano"}})
    help_ = bot.execute("help")

    assert start.text == "Hello, Joseano!"
    assert help_.text == "Available commands: start, help"


def test_bot_uses_commands_directory_by_default(tmp_path: Path, monkeypatch) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    (commands_dir / "start.yml").write_text(
        """
response:
  text: "Hello from the default directory!"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = Bot().execute("start")

    assert result.text == "Hello from the default directory!"


@pytest.mark.parametrize(
    "command_name",
    ["", ".", "..", ".hidden", "../outside", "nested/start", r"nested\start"],
)
def test_bot_rejects_invalid_command_names(tmp_path: Path, command_name: str) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    bot = Bot(commands_dir=commands_dir)

    with pytest.raises(InvalidCommandError, match="Invalid command name"):
        bot.execute(command_name)


def test_bot_rejects_missing_command_with_a_clear_error(tmp_path: Path) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    bot = Bot(commands_dir=commands_dir)

    with pytest.raises(
        CommandNotFoundError,
        match=r"Command file .+commands/missing\.yml not found",
    ):
        bot.execute("missing")
