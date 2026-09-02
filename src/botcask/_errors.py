class InvalidCommandError(ValueError):
    """Raised when a command file does not satisfy the BotCask contract."""


class CommandNotFoundError(FileNotFoundError):
    """Raised when a named command does not exist."""
