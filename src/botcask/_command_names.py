def is_valid_command_name(command_name: str) -> bool:
    return (
        bool(command_name)
        and command_name not in {".", ".."}
        and not command_name.startswith(".")
        and "/" not in command_name
        and "\\" not in command_name
    )
