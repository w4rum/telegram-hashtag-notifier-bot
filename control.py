#!/bin/python

import datetime
import sys
import time
import threading
import traceback
import signal
import logging
import html
import os.path
import pickle
import re
import operator

# Custom scripts
import telegrambot

# Config
import config

# Constants
CONFIG_FILE     = "config.py"

# Bot instance
tgBot           = None

# Subscription DB
subs            = {}

# General
def loadSubs():
    global subs
    if os.path.isfile(config.picklefile):
        with open(config.picklefile, "rb") as f:
            subs = pickle.load(f)

def saveSubs():
    with open(config.picklefile, "wb") as f:
        pickle.dump(subs, f)


### TG-Bot Commands
def toTG(s, raw=False):
    """Handles sending messages to the Telegram bot.
    The TG bot will simply send the message with HTML parsing enabled."""
    if not raw:
        tgBot.send(html.escape(s))
    else:
        tgBot.send(s)

def startTGBot():
    """Starts the Telegram bot and sets the global
    tgBot variable."""
    global tgBot
    tgBot = telegrambot.TGBot()
    tgBot.texthandlers += [onTGMessage]
    tgBot.addCommand("sub", cmdSub)
    tgBot.addCommand("unsub", cmdUnsub)
    tgBot.addCommand("list", cmdList)
    tgBot.addCommand("mysubs", cmdMySubs)
    tgBot.run()

def extractHt(update, expectHT=False):
    text = update.message['text']
    sender = update.message.from_user['id']
    senderName = update.message.from_user['username'] or sender

    htList = []
    htRaws = re.findall(r"#[a-zA-Z0-9]*(?=(?:\s+|$))", text)

    if len(htRaws) == 0 and expectHT:
        toTG("" +
"""No valid hashtag found.

Hashtags must be prefixed with a hash (#) and consist of alphanumeric \
characters only.

Examples: #csgo, #ArmA3""" % htRaw)
        return None

    for htRaw in htRaws:
        ht = htRaw[1:]
        htList.append((htRaw, ht))
    return htList, sender, senderName

def cmdSub(bot, update):
    ex = extractHt(update, expectHT=True)
    if ex == None:
        return
    htList, sender, senderName = ex

    goodList = []
    dupeList = []
    for htRaw, ht in htList:
        if ht not in subs:
            subs[ht] = set()
        if sender in subs[ht]:
            dupeList.append(htRaw)
        else:
            subs[ht].add(sender)
            goodList.append(htRaw)

    if len(dupeList) == 0:
        toTG("%s subscribed to %s" % (senderName, ", ".join(goodList)))
    else:
        toTG("%s subscribed to %s (was already subscribed to %s)" %
             (senderName, ", ".join(goodList), ", ".join(dupeList)))
    saveSubs()

def cmdUnsub(bot, update):
    ex = extractHt(update, expectHT=True)
    if ex == None:
        return
    htList, sender, senderName = ex

    goodList = []
    missList = []
    for htRaw, ht in htList:
        if (ht not in subs) or (sender not in subs[ht]):
            missList.append(htRaw)
        else:
            subs[ht].remove(sender)
            if len(subs[ht]) == 0:
                del subs[ht]
            goodList.append(htRaw)

    if len(missList) == 0:
        toTG("%s unsubscribed from %s" % (senderName, ", ".join(goodList)))
    else:
        toTG("%s unsubscribed from %s (was not subscribed to %s)" %
             (senderName, ", ".join(goodList), ", ".join(missList)))
    saveSubs()

def cmdList(bot, update):
    msg = "Known hashtags and subscriber count:\n"
    msg += "<pre>Count | Hashtag\n"
    msg += "----------------------\n"
    hts = []
    for ht, subset in subs.items():
        hts.append((ht, len(subset)))

    hts.sort(key=operator.itemgetter(1), reverse=True)

    for ht, count in hts:
        msg += "%5i | %s\n" % (count, ht)

    msg += "</pre>"

    toTG(msg, raw=True)

def cmdMySubs(bot, update):
    sender = update.message.from_user['id']
    senderName = update.message.from_user['username'] or sender

    hts = []
    for ht, subset in subs.items():
        if sender in subset:
            hts.append("#" + ht)

    msg = "%s is subscribed to %s" % (senderName, ", ".join(hts))
    toTG(msg)

def onTGMessage(text):
    """Handles receiving messages from the Telegram bot."""
    # find hashtags (hash (#) + alphanumeric chars + space or end-of-string)
    htsRaw = re.findall(r"#[a-zA-Z0-9]*(?=(?:\s+|$))", text)

    for htRaw in htsRaw:
        ht = htRaw[1:]
        if ht not in subs or len(subs[ht]) == 0:
            continue

        msg = ("%s was mentioned.\n" % htRaw) + " ".join([(
            '<a href="tg://user?id=%i">%i</a>' % (sender, sender))
            for sender in subs[ht]])
        toTG(msg, raw=True)

### Common
def quit():
    """Gracefully shuts down the bot"""
    global should_quit
    tgBot.stop()
    should_quit = True

### Main
if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG,
    #                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    COMMANDS_CLI    = {
        "quit": quit
    }

    should_quit = False

    # Load subscription DB
    loadSubs()

    try:
        startTGBot()
        while not should_quit:
            cmd = input("> ")
            if not cmd in COMMANDS_CLI:
                print("Unknown command!")
            else:
                COMMANDS_CLI[cmd]()

    except (KeyboardInterrupt, EOFError) as e:
        print("Interrupt received. Shutting down...")
        quit()

    except:
        print("====================")
        print("Main thread crashed!")
        print("====================")
        print()
        traceback.print_exc()


