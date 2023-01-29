import core.module
import core.command
import core.bot_instance
import core.irc_packet


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("botname", self.handle_mikrobi_command, 0, None,
                                 None))

    def handle_mikrobi_command(self, source, target, is_pm, args):
        self.bot.send_message(target, "<-")
