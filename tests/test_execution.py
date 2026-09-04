from pathlib import Path

import pytest
import yaml
from jinja2 import UndefinedError
from pydantic import ValidationError

from botcask import (
    CommandNotFoundError,
    CommandRenderError,
    InvalidCommandError,
    execute_command,
)


def test_command_renders_variables_from_context(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
message:
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
message:
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


def test_rejects_command_without_message_text_defined_in_yaml(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
        message: {}
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(InvalidCommandError):
        execute_command(command_path, context={})


def test_rejects_command_without_message_output_defined(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text("{}", encoding="utf-8")

    with pytest.raises(InvalidCommandError, match="Invalid command") as exc_info:
        execute_command(command_path, context={})

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ValidationError)


@pytest.mark.parametrize(
    "content",
    [
        """
message:
  text: 42
""",
        """
message:
  text: "Hello!"
  reply_markup:
    inline_keyboard:
      - - text: "Help"
""",
        """
message:
  text: "Hello!"
  reply_markup:
    inline_keyboard:
      - text: "Help"
        callback_data: "help"
""",
        """
message:
  text: "Hello!"
  reply_markup: {}
""",
        """
message:
  text: "Hello!"
metadata: {}
""",
    ],
)
def test_rejects_message_with_invalid_contract(tmp_path: Path, content: str) -> None:
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
message:
  text: "Welcome,
    """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(InvalidCommandError, match="malformed YAML") as exc_info:
        execute_command(command_path, context={})

    assert str(command_path.resolve()) in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, yaml.YAMLError)


def test_command_uses_message_defined_in_yaml(tmp_path: Path) -> None:
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


def test_command_exposes_telegram_inline_keyboard(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
message:
  text: "Choose an option"
  reply_markup:
    inline_keyboard:
      - - text: "Help"
          callback_data: "help"
        - text: "Profile"
          callback_data: "profile"
      - - text: "About"
          callback_data: "about"
""".strip(),
        encoding="utf-8",
    )

    result = execute_command(command_path)

    assert result.reply_markup is not None
    assert result.reply_markup.inline_keyboard[0][0].text == "Help"
    assert result.reply_markup.inline_keyboard[0][1].callback_data == "profile"
    assert result.reply_markup.inline_keyboard[1][0].text == "About"


def test_command_renders_inline_keyboard_templates(tmp_path: Path) -> None:
    command_path = tmp_path / "start.yml"
    command_path.write_text(
        """
message:
  text: "Choose an option"
  reply_markup:
    inline_keyboard:
      - - text: "{{ option.label }}"
          callback_data: "{{ option.command }}"
""".strip(),
        encoding="utf-8",
    )

    result = execute_command(
        command_path,
        context={"option": {"label": "Help", "command": "help"}},
    )

    assert result.reply_markup is not None
    button = result.reply_markup.inline_keyboard[0][0]
    assert button.text == "Help"
    assert button.callback_data == "help"


@pytest.mark.parametrize(
    "content",
    [
        """
message:
  text: "Hello!"
response:
  text: "Hello!"
""",
    ],
)
def test_rejects_legacy_response_contract(tmp_path: Path, content: str) -> None:
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
message:
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
