# BotCask

A declarative Python microframework that loads Telegram-shaped YAML command definitions, validates them against a strict contract, renders them with Jinja2, and maps results to the Telegram Bot API.

## Language

**Bot**:
The runtime entrypoint bound to a `Commands Directory` (defaulting to `commands/`) that validates a command name and delegates execution to `execute_command()`.
_Avoid_: Client, app, dispatcher, router

**Commands Directory**:
The root filesystem directory (`commands_dir`) containing declarative `<command_name>.yml` files; acts as a strict path-traversal boundary.
_Avoid_: Handlers folder, templates folder, scripts directory

**Command**:
A named bot action defined declaratively in a `<command_name>.yml` file inside the `Commands Directory`.
_Avoid_: Handler, endpoint, route, skill

**CommandSpec**:
The strict Pydantic root schema (`extra="forbid"`, `strict=True`) representing a declarative `Command` file containing a `MessageSpec`.
_Avoid_: CommandPayload, CommandConfig, YAMLSchema

**MessageSpec**:
The Telegram-shaped message definition inside a `CommandSpec` (`message.text` and optional `message.reply_markup`); replaced the earlier `response.text` schema.
_Avoid_: ResponseSpec, OutputConfig, ReplyTemplate

**InlineKeyboardMarkup / InlineKeyboardButton**:
The Telegram-shaped inline keyboard structure (`inline_keyboard` rows of buttons with `text` and `callback_data`) attached to a `MessageSpec` and preserved on `CommandResult`.
_Avoid_: ActionButtons, MenuMarkup, ReplyButtons

**Execution Context**:
The dictionary of runtime variables (such as `user`, `chat`, `message`, and `callback_query`, often produced by `telegram_context(update)`) passed into `execute()` / `execute_command()` for strict Jinja2 rendering.
_Avoid_: State, session, env

**CommandResult**:
The immutable value object (`text` and optional `reply_markup`) returned after validating and rendering a `CommandSpec`; marks the boundary between the declarative runtime and the `TelegramProvider`.
_Avoid_: BotResponse, ExecutionOutput, Reply

**TelegramProvider**:
The outbound adapter boundary responsible for converting a `CommandResult` and `chat_id` (via `build_send_message_payload()`) and delivering it to the Telegram Bot API `sendMessage` endpoint without leaking HTTP, token, or transport concerns into the declarative runtime.
_Avoid_: TelegramClient, BotRunner, WebhookHandler
