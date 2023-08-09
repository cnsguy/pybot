import core.module
import core.command
import core.bot_instance
import core.irc_packet
import re


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_event("core.message", self.handle_message)

    def handle_message(self, user_source, reply_target, is_pm, message):
        # XXX could be simplified now that sender nick isn't tracked - or could be restored into a form where it does in fact supply the right sender (strip colors)
        if user_source.nick != "shitcord" or is_pm:
            return

        match = re.match('^<[^>]+> (.*)$', message)

        if match is None:
            return

        post = match.group(1)

        if not post.startswith(self.bot.nick):
            return

        module = self.bot.module_instances.get("talkbot")

        if module is None:
            return

        result = module.run_talk(post)
        self.bot.send_message(reply_target, result)
