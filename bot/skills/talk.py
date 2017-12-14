from .base import BaseSkill


class Skill(BaseSkill):

    title = 'Поговорить'
    id = 'talk'


    def __init__(self, bot):
        super().__init__(bot)
        self.boss_name = None


    def on_message(self, update):

        if self.state is None:
            chat = update['message']['chat']
            self.bot.send_message(text='Привет, ' + chat['first_name'] + ' ' + chat['last_name'])
            if self.boss_name is None:
                self.bot.send_message(text="Как мне тебя называть?")
            self.state = 'ожидаю имя босса'

        elif self.state == 'ожидаю имя босса':
            self.boss_name = update['message']['text']
            self.bot.send_message(text='Хорошо, ' + self.boss_name)
            self.state = 'поговорить'

        elif self.state == 'поговорить':
            self.bot.send_message(text='Привет, ' + self.boss_name)
