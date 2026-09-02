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