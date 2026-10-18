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
4. `TelegramProvider` translates `CommandResult` into a synchronous Telegram
   Bot API `sendMessage` request.

```python
from botcask import Bot, TelegramProvider, telegram_context

bot = Bot()
provider = TelegramProvider("123456:BOT-TOKEN")

context = telegram_context(update)
result = bot.execute("start", context=context)
telegram_message = provider.send(context["chat"]["id"], result)
```

The provider boundary starts at `CommandResult`. `TelegramProvider` receives a
Telegram `chat_id` (`int` or non-empty `str`) and a `CommandResult`, sends the
rendered text and optional inline keyboard through `sendMessage` with an
explicit timeout (`timeout=10.0` by default), and returns the decoded Telegram
`result` dictionary without mutating `CommandResult` or exposing the bot token
in string representations or errors.

Commands can still be fully tested with local fixtures and contexts without
Telegram credentials or network access.

**MVP limitations:** `TelegramProvider` is an outbound `sendMessage` boundary
only. Command routing, update polling, webhook servers, media uploads, callback
query acknowledgements (`answerCallbackQuery`), async clients, and automatic
retry loops are out of scope.

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

BotCask exposes distinct public errors for command execution and Telegram
provider failures:

```python
from botcask import (
    CommandNotFoundError,
    CommandRenderError,
    InvalidCommandError,
    TelegramAPIError,
    TelegramTransportError,
)
```

- `CommandNotFoundError`: raised when the command file does not exist.
- `InvalidCommandError`: raised when the command name is invalid (empty,
  dot-prefixed, or path-like), when the command file is not valid YAML, or when
  it does not match the supported command contract.
- `CommandRenderError`: raised when rendering fails because the provided context
  is missing values referenced by the template.
- `TelegramAPIError`: raised when the Telegram Bot API returns `ok: false`;
  exposes `error_code`, `description`, and `retry_after` (when returned in
  `parameters.retry_after`) without performing automatic retries.
- `TelegramTransportError`: raised when a Telegram Bot API request fails due to
  network errors, timeouts, malformed JSON, or an unexpected response envelope.

Errors include the command file path when available and never expose the bot
token, so failures remain safe and actionable.