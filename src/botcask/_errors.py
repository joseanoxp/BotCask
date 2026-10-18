class InvalidCommandError(ValueError):
    """Raised when a command file does not satisfy the BotCask contract."""


class CommandNotFoundError(FileNotFoundError):
    """Raised when a named command does not exist."""


class CommandRenderError(ValueError):
    """Raised when a command cannot be rendered from the provided context."""


class TelegramAPIError(RuntimeError):
    """Raised when the Telegram Bot API returns an ok=false response."""

    def __init__(
        self,
        description: str,
        *,
        error_code: int | None = None,
        retry_after: int | None = None,
    ) -> None:
        self.error_code = error_code
        self.description = description
        self.retry_after = retry_after

        details: list[str] = []
        if error_code is not None:
            details.append(f"error_code={error_code}")
        if retry_after is not None:
            details.append(f"retry_after={retry_after}")

        prefix = (
            f"Telegram Bot API error ({', '.join(details)})"
            if details
            else "Telegram Bot API error"
        )
        super().__init__(f"{prefix}: {description}")


class TelegramTransportError(RuntimeError):
    """Raised when a Telegram Bot API request fails due to transport or response decoding."""
