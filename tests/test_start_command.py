from pathlib import Path

import pytest

from botcask import (
    Bot,
    CommandNotFoundError,
    InvalidCommandError,
    execute_command,
)


def test_command_renders_variables_from_context(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
response:
  text: "Welcome to {{ chat.title }}, {{ user.first_name }}!"
""".strip(),
        encoding="utf-8",
    )

    result = execute_command(
        command_path,
        context={
            "user": {"first_name": "Alice"},
            "chat": {"title": "BotCask"},
        },
    )

    assert result.text == "Welcome to BotCask, Alice!"


def test_rejects_command_without_response_text_defined_in_yaml(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
        response: {}
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(InvalidCommandError):
        execute_command(command_path, context={})


def test_rejects_malformed_yaml_as_invalid_command(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
response:
  text: "Welcome,
    """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(InvalidCommandError, match="Invalid command"):
        execute_command(command_path, context={})


def test_command_uses_response_defined_in_yaml(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
        response:
          text: "Welcome, {{ user.first_name }}!"
        """.strip(),
        encoding="utf-8",
    )

    result = execute_command(command_path, context={"user": {"first_name": "Alice"}})

    assert result.text == "Welcome, Alice!"


@pytest.mark.parametrize(
    ("first_name", "expected"),
    [
        ("Joseano", "Hello, Joseano!"),
        ("Alice", "Hello, Alice!"),
        ("Bob", "Hello, Bob!"),
    ],
)
def test_start_command_greets_the_user(first_name: str, expected: str) -> None:
    result = execute_command(
        "examples/hello/commands/start.yml",
        context={"user": {"first_name": first_name}},
    )

    assert result.text == expected


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
        match=r"Command 'missing' not found in .+commands",
    ):
        bot.execute("missing")
