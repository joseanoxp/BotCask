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

Commands currently use this contract:

```yaml
response:
  text: "Hello, {{ user.first_name }}!"
```

`response.text` is required and must be a string. Unknown fields and invalid
values are rejected.

## Runtime errors

BotCask exposes distinct public errors for the main command execution failures:

```python
from botcask import CommandNotFoundError, CommandRenderError, InvalidCommandError
```

- `CommandNotFoundError`: raised when the command file does not exist.
- `InvalidCommandError`: raised when the command file is not valid YAML or does
  not match the supported command contract.
- `CommandRenderError`: raised when a valid command cannot be rendered with the
  provided context, such as when a template variable is missing.

Errors include the command file path when available, so failures remain
actionable as projects add more command files.