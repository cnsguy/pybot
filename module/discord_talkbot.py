import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_bot_event("core.message", self.handle_message)

    def handle_message(self, user_source, reply_target, is_pm, message):
        # XXX could be simplified now that sender nick isn't tracked - or could be restored into a form where it does in fact supply the right sender (strip colors)
        if user_source.nick != "DiscordIRC" or is_pm:
            return

        if ":" not in message:
            return

        pre_splt = message.split(":")

        if len(pre_splt) < 2:
            return

        pre = pre_splt.pop(0)
        post = ":".join(pre_splt).lstrip()
        splt = pre.split(" ")

        if len(splt) < 2:
            return

        channel = splt.pop()

        if not channel.startswith("#"):
            return

        if not post.startswith(self.bot.nick):
            return

        module = self.bot.module_instances.get("talkbot")

        if module is None:
            return

        result = module.run_talk(post)
        self.bot.send_message(reply_target, "~msg %s %s" % (channel, result))