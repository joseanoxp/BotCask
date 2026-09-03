from pathlib import Path

import pytest
import yaml
from jinja2 import UndefinedError
from pydantic import ValidationError

from botcask import (
    CommandAction,
    CommandNotFoundError,
    CommandRenderError,
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


def test_command_renders_without_context_when_template_has_no_variables(
    tmp_path: Path,
) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
response:
  text: "Welcome to BotCask!"
""".strip(),
        encoding="utf-8",
    )

    result = execute_command(command_path)

    assert result.text == "Welcome to BotCask!"


def test_rejects_missing_command_file_with_a_clear_error(tmp_path: Path) -> None:
    command_path = tmp_path / "missing.yml"

    with pytest.raises(
        CommandNotFoundError,
        match=rf"Command file {command_path} not found",
    ) as exc_info:
        execute_command(command_path, context={})

    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


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


@pytest.mark.parametrize(
    "content",
    [
        """
response:
  text: 42
""",
        """
response:
  text: "Hello!"
  keyboard: []
""",
        """
response:
  text: "Hello!"
metadata: {}
""",
    ],
)
def test_rejects_response_with_invalid_contract(tmp_path: Path, content: str) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(InvalidCommandError, match="Invalid command") as exc_info:
        execute_command(command_path, context={})

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_rejects_malformed_yaml_as_invalid_command(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
response:
  text: "Welcome,
    """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(InvalidCommandError, match="malformed YAML") as exc_info:
        execute_command(command_path, context={})

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, yaml.YAMLError)


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
    assert result.actions == ()


def test_command_uses_telegram_message_text_defined_in_yaml(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
message:
  text: "Welcome, {{ user.first_name }}!"
""".strip(),
        encoding="utf-8",
    )

    result = execute_command(command_path, context={"user": {"first_name": "Alice"}})

    assert result.text == "Welcome, Alice!"
    assert result.actions == ()


@pytest.mark.parametrize(
    "content",
    [
        """
message: {}
""",
        """
message:
  text: 42
""",
        """
message:
  text: "Hello!"
  reply_markup: {}
""",
        """
message:
  text: "Hello!"
response:
  text: "Hello!"
""",
    ],
)
def test_rejects_telegram_message_with_invalid_contract(
    tmp_path: Path, content: str
) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(InvalidCommandError, match="Invalid command") as exc_info:
        execute_command(command_path)

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_command_returns_response_actions(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
response:
  text: "Choose the next step"
  actions:
    - label: "Show help"
      command: "help"
    - label: "Start again"
      command: "start"
""".strip(),
        encoding="utf-8",
    )

    result = execute_command(command_path)

    assert result.text == "Choose the next step"
    assert result.actions == (
        CommandAction(label="Show help", command="help"),
        CommandAction(label="Start again", command="start"),
    )


@pytest.mark.parametrize(
    "content",
    [
        """
response:
  text: "Choose"
  actions:
    - command: "help"
""",
        """
response:
  text: "Choose"
  actions:
    - label: "Help"
      command: "../help"
""",
        """
response:
  text: "Choose"
  actions:
    - label: 42
      command: "help"
""",
        """
response:
  text: "Choose"
  actions:
    - label: "Help"
      command: "help"
      payload: {}
""",
    ],
)
def test_rejects_response_actions_with_invalid_contract(
    tmp_path: Path, content: str
) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(InvalidCommandError, match="Invalid command") as exc_info:
        execute_command(command_path)

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_rejects_missing_template_context_with_a_clear_error(
    tmp_path: Path,
) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
response:
  text: "Welcome, {{ user.first_name }}!"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        CommandRenderError, match="Failed to render command"
    ) as exc_info:
        execute_command(command_path, context={})

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, UndefinedError)


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
