from ast import arg
from telegram.ext import Updater, CommandHandler
from configparser import ConfigParser
import logging
import os 
from sys import argv
import back

config = ConfigParser()
configfile = 'bot.conf'

config.read(f"./{configfile}")
settings = config['SETTING_BOT']
token = settings['token']

def start(update, context):
    update.message.reply_text("Hi i'm a live")

def truncated_msg(text):
    if len(text) >= 4000:
        result = f"{text[:4000]}... \n \n"
        result += f"MESSAGE TRUNCATED DUE TO TELEGRAM MAX MESSAGE LENGTH"
        return result
    else:
        return text

def count(update, context):
    update.message.reply_text(f"Hello!  Give me a few moments to run your request.  This could take a bit.")
    text = back.check_config()
    msg = truncated_msg(text)
    update.message.reply_text(msg)

def oldest(update, context):
    args = context.args
    if len(args) == 0:
        text = back.check_oldest()
        msg = truncated_msg(text) 
        update.message.reply_text(msg)
    elif len(args) > 1:
        text = "Too many arguments.  Please only provide one argument."
        msg = truncated_msg(text)
        update.message.reply_text(text)
    else:
        args = args[0]
        if int(args) > 0 :
            text = back.check_oldest(int(args))
            msg = truncated_msg(text)
            update.message.reply_text(msg)
        else:
            text = "Please enter a valid number"
            msg = truncated_msg(text)
            update.message.reply_text(msg)

def oldestByUser (update, context):
    text = back.check_oldest_by_user()
    msg = truncated_msg(text)
    update.message.reply_text(msg)

def help(update, context):
    msg = "/help = List all available commands to implement \n"
    msg +="/oldestbyuser = Oldest file for each user on the team. \n"
    msg += "/oldest [X] = Absolute oldest file[s] not placed. \n"
    msg += "/count = List of all users and the quantity of scans  remaining in each of their folders. \n"
    msg += "/scansoverdays [X] = Send a list of files from all users of X days old.  Null if none exist. \n"
    msg += "/scansOverDays [X] = Send a list of files from all users of X days old.  Null if none exist."
    msg += "/info = SCAN BOT information"
    text = truncated_msg(msg)    
    update.message.reply_text(text)

def info(update, context):
    text = f'''NOTES:
- The IM SCAN BOT 

1) ignores any folder named "PERSONAL" and will not look within it (case insensative).
2) was rolled out on the "REPORTS" server (192.168.200.221).  


Copyright 2022, Iconic Mind.  All rights reserved.  Property of Iconic Mind.   '''
    
    msg = truncated_msg(text)
    update.message.reply_text(msg)

def scansOverDays(update, context):
    args = context.args
    if len(args) == 0:
        text = "NOTE: No day argument provided.  10 days is our default.\n"
        result = back.check_oldest_by_day()
        if result == None:
            text = "No files found."
        else:
            text = result
        msg = truncated_msg(text)
        update.message.reply_text(msg)
    elif len(args) > 1:
        msg = "Too many arguments provided just one argument is needed"
        update.message.reply_text(msg)

    else:
        args = args[0]
        if  int(args) > 0 and int(args) < 3 :
                text = "The minimum number of days is 3.\n"
                text += "Here are the results: \n"
                result = back.check_oldest_by_day(args)
                if result == None:
                    text += "No files found"
                else:
                    text += result
                msg = truncated_msg(text)
                update.message.reply_text(msg)

        elif int(args) >= 3:
            result = back.check_oldest_by_day(args)
            if result == None:
                text = "No files found"
            else:
                text = result
            msg = truncated_msg(text)
            update.message.reply_text(msg) 
        else:
            text = "Please enter a valid number, The minimum number must be 3"
            msg = truncated_msg(text)
            update.message.reply_text(msg)

def testingOverDays(update, context):
    if(back.check_oldest_by_day(12)!= None):
        text = f"URGENT: Files found in the last 12 days.  Please review.\n"
        text += back.checkUserDaysDelay(12)
    elif(back.check_oldest_by_day(9)!= None):
        text = f"IMPORTANT: Files found in the last 9 days.  Please review.\n"
        text += back.checkUserDaysDelay(9)
    elif(back.check_oldest_by_day(6)!= None):
        text = f"WARNING: Files found in the last 6 days.  Please review.\n"
        text += back.checkUserDaysDelay(6)
    msg = truncated_msg(text)
    update.message.reply_text(msg)

if __name__ == '__main__':
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('count', count))
    dispatcher.add_handler(CommandHandler('oldest', oldest))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('helpme', help))
    dispatcher.add_handler(CommandHandler('info', info))
    dispatcher.add_handler(CommandHandler('scansoverdays', scansOverDays))
    dispatcher.add_handler(CommandHandler('oldestbyuser', oldestByUser))
    dispatcher.add_handler(CommandHandler('testingdays', testingOverDays))
    updater.start_polling()
    print('Bot started')
    updater.idle()
