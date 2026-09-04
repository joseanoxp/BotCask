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

Commands use the minimal Telegram-shaped message contract:

```yaml
message:
  text: "Hello, {{ user.first_name }}!"
```

`message.text` is required and must be a string. Unknown fields and invalid
values are rejected. The previous `response.text` contract is no longer
supported because Telegram is BotCask's primary provider.

Inline keyboards use Telegram's nested provider shape. The current subset
requires each button to have `text` and `callback_data`:

```yaml
message:
  text: "Choose an option"
  reply_markup:
    inline_keyboard:
      - - text: "Help"
          callback_data: "help"
```

The public result exposes the rendered text and, when configured, the
provider-shaped inline keyboard:

```python
print(result.text)
print(result.reply_markup.inline_keyboard[0][0].callback_data)
```

## Telegram provider boundary

The runtime is deliberately split from Telegram transport:

1. `execute_command()` loads and validates the YAML contract.
2. The runtime renders all templates using the supplied context.
3. `CommandResult` carries the rendered, Telegram-shaped message data.
4. A future `TelegramProvider` will translate `CommandResult` into Telegram
   Bot API requests.

The provider boundary starts at `CommandResult`. The future
`TelegramProvider` may receive a destination such as a Telegram chat ID and
will be responsible for HTTP requests, tokens, retries, and transport errors.
None of those concerns belong in YAML loading, schema validation, or template
rendering.

Until that provider is implemented, commands can be fully tested with local
fixtures and contexts. No Telegram credentials, network access, webhook, or
polling loop is required to validate the declarative runtime.

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

Telegram updates can be mapped into this context with `telegram_context()`.
The mapper preserves Telegram's `message` and `callback_query` objects and
exposes the originating `from` and `chat` objects as `user` and `chat`:

```python
from botcask import telegram_context

context = telegram_context(update)
result = bot.execute("start", context=context)
```

For message updates, templates can consume `message.text` or
`message.caption`. For callback queries, they can consume
`callback_query.data`; `user` and `chat` are taken from the originating
Telegram object. Missing fields remain absent, so referencing them raises
`CommandRenderError`. The mapper is a pure local transformation and does not
download media or make Telegram API requests.

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