import core.module
import core.command
import core.bot_instance
import core.irc_packet
from random import choice

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("choice", self.handle_choice_command, 1, "<lehetosegek...>",
                "Valaszt a lehetosegek kozul."))

    def handle_choice_command(self, source, target, was_pm, args):
        joined = " ".join(args)
        possible = joined.split(",")
        result = choice(possible).strip()
        self.bot.send_message(target, result)