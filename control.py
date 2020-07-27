#!/bin/python

import sys
import traceback
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
CONFIG_FILE = "config.py"

# Bot instance
tgBot = None

# Subscription DB
subs = {}

logger: logging.Logger = None


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
    regex = r"#[a-zA-Z0-9]*(?=(?:\s+|$|[^a-zA-Z0-9]))"
    htRaws = re.findall(regex, text)
    htRaws = [x.lower() for x in htRaws]

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


def cmdSub(update, context):
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


def cmdUnsub(update, context):
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


def cmdList(update, context):
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


def cmdMySubs(update, context):
    sender = update.message.from_user['id']
    senderName = update.message.from_user['username'] or sender

    hts = []
    for ht, subset in subs.items():
        if sender in subset:
            hts.append("#" + ht)

    msg = "%s is subscribed to %s" % (senderName, ", ".join(hts))
    toTG(msg)


def onTGMessage(update, context):
    """Handles receiving messages from the Telegram bot."""
    # find hashtags (hash (#) + alphanumeric chars + space or end-of-string)
    ex = extractHt(update, expectHT=False)
    if ex == None:
        return
    htList, sender, senderName = ex

    for htRaw, ht in htList:
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


def setup_logging(*, debug_on_stdout=False) -> None:
    """
    Sets up multiple log files with different sensitivities.
    INFO will also be sent to stdout.
    WARNING and above will also be sent to stderr.
    DEBUG will only be sent to stdout if debug_on_stdout is True.

    :param debug_on_stdout: Whether DEBUG should be logged on stdout
    """

    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s][%(funcName)s] %(message)s")

    # multiple files with different sensitivities
    os.makedirs("logs", exist_ok=True)
    log_debug = logging.FileHandler(filename="logs/debug.log",
                                    encoding="utf-8", mode="a")
    log_debug.setLevel(logging.DEBUG)
    log_debug.setFormatter(formatter)
    log_info = logging.FileHandler(filename="logs/info.log",
                                   encoding="utf-8", mode="a")
    log_info.setLevel(logging.INFO)
    log_info.setFormatter(formatter)
    log_warning = logging.FileHandler(filename="logs/warning.log",
                                      encoding="utf-8", mode="a")
    log_warning.setLevel(logging.WARNING)
    log_warning.setFormatter(formatter)

    stdout_level = logging.DEBUG if debug_on_stdout else logging.INFO
    log_stdout = logging.StreamHandler(stream=sys.stdout)
    log_stdout.setLevel(stdout_level)
    log_stdout.setFormatter(formatter)

    log_stderr = logging.StreamHandler(stream=sys.stderr)
    log_stderr.setLevel(logging.WARNING)
    log_stderr.setFormatter(formatter)

    # filter WARNING and above on stdout
    def filter_above_info(record):
        return record.levelno <= logging.INFO

    log_stdout.addFilter(filter_above_info)

    logging.basicConfig(level=logging.NOTSET,
                        handlers=[log_debug, log_info, log_warning, log_stdout,
                                  log_stderr])

    global logger
    logger = logging.getLogger(__name__)


### Main
if __name__ == "__main__":
    setup_logging(debug_on_stdout=True)

    # Load subscription DB
    loadSubs()

    try:
        startTGBot()
    except (KeyboardInterrupt, EOFError) as e:
        print("Interrupt received. Shutting down...")
        quit()
    except:
        print("====================")
        print("Main thread crashed!")
        print("====================")
        print()
        traceback.print_exc()
