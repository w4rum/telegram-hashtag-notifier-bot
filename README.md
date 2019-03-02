# About

This bot allows group members to subscribe to hashtags.
Whenever someone mentions a hashtag in a group message, the bots automatically
mentions all users that are subscribed to that hashtag.

This is useful if you only want notifications for a certain subset of messages,
e.g. you're in a gaming group but only want messages for #rimworld.

# Installation

1. Clone the repository
2. Create a bot on Telegram by messaging @BotFather and following the instructions.
3. Disable Private Mode for the bot by messaging @BotFather.
4. Copy `config.py.sample` to `config.py`
5. Change the Telegram API token in `config.py` and start the bot
6. Add the bot to your group and use `/start`
7. Change the Telegram chat ID in `config.py` and restart the bot

# Usage

To start the bot, run `python3 control.py`.

The control interface also supports the following commands:
- `quit`: Gracefully shuts the bot down.
