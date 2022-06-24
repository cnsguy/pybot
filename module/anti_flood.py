import core.module
import core.command
import core.bot_instance
import core.irc_packet
from string import ascii_uppercase

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_event("core.message", self.handle_message)
        self.blog_counter = 0
        self.num_kicks = 0
        self.last_host = None

    def reset_counters(self):
        self.blog_counter = 0
        self.num_kicks = 0

    def handle_message(self, user_source, reply_target, is_pm, message):
        if is_pm:
            return

        if user_source.host != self.last_host:
            self.reset_counters()
        
        self.last_host = user_source.host

        # Only trigger for that one obnoxious guy who floods the channel with barely coherent garbage
        if not user_source.host.endswith("catv.fixed.vodafone.hu"):
            self.reset_counters()
            return

        # Only increment blog counter if the messages are uppercase (he always does this)
        for ch in ascii_uppercase:
            if message.startswith(ch):
                self.blog_counter += 1
                break

        if self.blog_counter >= 5:
            self.bot.send_raw_line("KICK %s %s :Stop flooding (Sorry if false positive)" % (reply_target, user_source.nick))
            self.num_kicks += 1
            self.blog_counter = 0

        if self.num_kicks >= 3:
            self.bot.send_raw_line("MODE %s +b %s" % (reply_target, user_source.host))