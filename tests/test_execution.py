from pathlib import Path

import pytest
import yaml
from jinja2 import UndefinedError

from botcask import CommandRenderError, InvalidCommandError, execute_command


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

    with pytest.raises(
        InvalidCommandError, match="Invalid command: malformed YAML"
    ) as exc_info:
        execute_command(command_path, context={})

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
