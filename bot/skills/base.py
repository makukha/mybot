class BaseSkill:


    def __init__(self, bot):
        self.bot = bot
        self.state = None


    @property
    def allowed_usernames(self):
        """List all allowed usernames, ['*'] means everyone
        """
        allowed = getattr(self, 'allow', [])
        if '*' in allowed:
            return ['*']
        else:
            return list(sorted(set(allowed + [self.bot.telegram_master])))

    def end_session(self):
        """End skill application session
        """
        self.bot.skill = None
