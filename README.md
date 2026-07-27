# BotCask

BotCask — a small Python framework for building bots from declarative files.

## Quick example

```python
from botcask import Bot

bot = Bot(commands_dir="commands")
result = bot.execute("start", context={"user": {"first_name": "Joseano"}})
print(result.text)
```