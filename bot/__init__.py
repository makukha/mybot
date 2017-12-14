try:
    import unzip_requirements
except ModuleNotFoundError:
    pass

import base64
import boto3
import configparser
from datetime import datetime
import io
import json
import pathlib
import pickle
import queue
import telegram
import telegram.ext
import traceback


class PersonalBot:


    DONT_UNDERSTAND = 'Простите, не понимаю'
    TTL = 15


    def __init__(self, config):

        self.config = config
        self.aws_credentials = {k:self.config[k] for k in (
            'region_name',
            'aws_access_key_id',
            'aws_secret_access_key',
            )}

        # load skills
        from bot.skills import skills
        self.skills = skills

        # connect to Telegram channel
        self.telegram_bot = telegram.Bot(self.config['telegram_bot_token'])
        self.telegram_queue = queue.Queue()
        self.telegram_dispatcher = telegram.ext.Dispatcher(self.telegram_bot, self.telegram_queue, workers=1)
        self.telegram_dispatcher.add_handler(telegram.ext.CommandHandler('start', lambda bot, update: self.command_start(update)))
        self.telegram_dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, lambda bot, update: self.on_message(update)))
        self.telegram_dispatcher.add_error_handler(lambda bot, update, error: self.on_error(update, error))

        # connect to AWS resources
        self.aws_dynamodb = boto3.client('dynamodb', **self.aws_credentials)

        # state
        self.clear()


    def clear(self):
        """Initialize state with empty values
        """
        self.username = None
        self.chatid = None
        self.skill = None


    def skill_from_message(self, text):
        """Get skill instance by user message
        """
        for skill in self.skills:
            if skill.title == text:
                return skill


    def wake(self, update):
        """Wake up bot
        """
        self.username = update.effective_user.id
        self.chatid = update['message']['chat']['id']
        try:
            result = self.aws_dynamodb.get_item(TableName=self.config['mybot_table'], Key={'chatid': {'S': str(self.chatid)}})
            skillpickle = result['Item']['skill']['S']
            self.skill = pickle.loads(base64.b64decode(skillpickle))
            if self.skill is not None:
                self.skill.bot = self
        except:
            self.skill = None


    def sleep(self):
        """Save bot state
        """
        if self.skill is not None:
            self.skill.bot = None
        skillpickle = base64.b64encode(pickle.dumps(self.skill)).decode('ascii')
        item = {
            'chatid': {'S': str(self.chatid)},
            'skill': {'S': skillpickle},
            'ttl': {'S': str(int(datetime.utcnow().timestamp()) + self.TTL)},
            }
        self.aws_dynamodb.put_item(TableName=self.config['mybot_table'], Item=item)
        self.clear()


    def command_start(self, update):
        """Telegram command /start
        """
        try:
            # if update.effective_user.id != self.telegram_master:
            #     return
            self.wake(update)
            self.skill = None
            self.send_message(
                text='Чем я могу помочь?',
                reply_markup=telegram.ReplyKeyboardMarkup([[s.title] for s in self.skills]))
            self.sleep()
        except:
            self.chatid = update['message']['chat']['id']
            f = io.StringIO()
            traceback.print_exc(file=f)
            self.send_message(text=f.getvalue())


    def on_error(self, update, error):
        """Telegram error handler
        """
        update.message.reply_text(f'Update "{update}" caused error "{error}"')


    def on_message(self, update):
        """Telegram message handler
        """
        try:
            # if update.effective_user.id != self.telegram_master:
            #     return
            self.wake(update)
            newskills = [s for s in self.skills if s.title == update['message']['text']]
            if len(newskills):
                self.skill = newskills[0](bot=self)
            if self.skill is not None:
                self.skill.on_message(update)
                self.sleep()
            else:
                self.send_message(text=self.DONT_UNDERSTAND)
        except:
            self.chatid = update['message']['chat']['id']
            f = io.StringIO()
            traceback.print_exc(file=f)
            self.send_message(text=f.getvalue())


    def send_message(self, **kwargs):
        """Send Telegram message
        """
        self.telegram_bot.send_message(chat_id=self.chatid, **kwargs)


    def handle_telegram(self, event, context):
        """Bot handler for Telegram channel
        """
        body = json.loads(event['body'])
        update = telegram.Update.de_json(body, self.telegram_bot)
        bot.telegram_dispatcher.process_update(update)
        return {'statusCode': 200}


configfile = configparser.ConfigParser()
configfile.read(pathlib.Path(__file__).parent.parent / 'credentials')
config = configfile['serverless-mybot']

bot = PersonalBot(config)


# AWS API Gateway webhook handlers

def handle_telegram(event, context):
    return bot.handle_telegram(event, context)
