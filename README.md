# BotCask

BotCask — a small Python framework for building bots from declarative files.

## Quick example

```python
from botcask import Bot

bot = Bot()
result = bot.execute("start", context={"user": {"first_name": "Joseano"}})
print(result.text)
```

By default, `Bot` discovers commands in the `commands/` directory. A custom
directory can be provided with `Bot(commands_dir="path/to/commands")`.

Command names map directly to YAML files:

```text
commands/start.yml -> bot.execute("start")
commands/help.yml  -> bot.execute("help")
```

Commands can use the minimal Telegram-shaped message contract:

```yaml
message:
  text: "Hello, {{ user.first_name }}!"
```

`message.text` is required and must be a string. This is the preferred
declarative shape because Telegram is BotCask's primary provider.

The previous response contract is still supported during the transition:

```yaml
response:
  text: "Hello, {{ user.first_name }}!"
  actions:
    - label: "Show help"
      command: "help"
```

A command must define exactly one output: either `message` or `response`.
`response.text` is required and must be a string. `response.actions` is optional
and contains platform-agnostic actions with a `label` and a command name.
Unknown fields and invalid values are rejected.

The public result exposes the rendered text and actions:

```python
print(result.text)
print(result.actions)
```

## Context

Templates are rendered with the optional `context` dictionary passed to
`execute_command()` or `Bot.execute()`:

```python
result = bot.execute(
    "start",
    context={
        "user": {"first_name": "Joseano"},
        "chat": {"title": "BotCask"},
    },
)
```

Nested dictionaries can be referenced from YAML templates with dot notation:

```yaml
message:
  text: "Welcome to {{ chat.title }}, {{ user.first_name }}!"
```

The context may be omitted when the template does not reference variables.
Missing referenced values raise `CommandRenderError`.

## Runtime errors

BotCask exposes distinct public errors for the main command execution failures:

```python
from botcask import CommandNotFoundError, CommandRenderError, InvalidCommandError
```

- `CommandNotFoundError`: raised when the command file does not exist.
- `InvalidCommandError`: raised when the command name is invalid (empty,
  dot-prefixed, or path-like), when the command file is not valid YAML, or when
  it does not match the supported command contract.
- `CommandRenderError`: raised when rendering fails because the provided context
  is missing values referenced by the template.

Errors include the command file path when available, so failures remain
actionable as projects add more command files.