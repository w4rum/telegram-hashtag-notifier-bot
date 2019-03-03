#!/bin/python

# This is based on
# https://github.com/python-telegram-bot/python-telegram-bot (GPLv3 License)

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

import config

def _onStart(bot, update):
    if config.CHAT_ID != -1:
        bot.send_message(chat_id=update.message.chat_id,
                        text="This bot has already been configured.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                        text="Your CHAT_ID is %i. Add this to your config file."
                             % update.message.chat_id)

class TGBot():

    def __init__(self):
        self._updater = Updater(token=config.API_TOKEN)
        self._dispatcher = self._updater.dispatcher
        self._dispatcher.add_handler(CommandHandler('start', _onStart))
        self._dispatcher.add_handler(MessageHandler(Filters.text, self._onText))
        self.texthandlers = []

    def run(self):
        self._updater.start_polling()

    def stop(self):
        self._updater.stop()
        print("Telegram Bot shut down.")

    def _onText(self, bot, update):
        chat_id = update.message.chat_id
        if chat_id != config.CHAT_ID:
            return
        for handler in self.texthandlers:
            handler(bot, update)

    def send(self, text):
        self._updater.bot.send_message(
            chat_id=config.CHAT_ID,
            text=text,
            parse_mode=telegram.ParseMode.HTML
        )

    def addCommand(self, command, handler):
        # Wrap the handler to include a CHAT_ID check
        self._dispatcher.add_handler(CommandHandler(command,
            lambda bot, update: self._commandWrapper(handler, bot, update)))

    def _commandWrapper(self, handler, bot, update):
        chat_id = update.message.chat_id
        if chat_id != config.CHAT_ID:
            return
        else:
            return handler(bot, update)

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG,
    #                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    bot = TGBot()
    bot.run()
