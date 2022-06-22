import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_event("core.message", self.handle_message)

    def handle_message(self, user_source, reply_target, is_pm, message):
        if user_source.nick != "discord2irc" or is_pm:
            return

        if ":" not in message:
            return

        splt = message.split(" ")

        if len(splt) < 2:
            return

        sender = splt.pop(0)
        message = " ".join(splt)

        if not message.startswith(self.bot.nick):
            return

        module = self.bot.module_instances.get("talkbot")

        if module is None:
            return

        result = module.run_talk(message)
        self.bot.send_message(reply_target, result)