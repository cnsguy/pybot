import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("say", self.handle_say_command, 0, "<uzenet...>",
                "Kuld egy uzenetet a jelenlegi csatornara.", "say.say"))
        self.register_command(
            core.command.Command("say_to", self.handle_say_to_command, 1, "<csatorna> <uzenet...>",
                "Kuld egy uzenetet a megadott csatornara.", "say.say"))
        self.register_command(
            core.command.Command("raw", self.handle_raw_command, 0, "<uzenet...>",
                "Kuld egy raw parancsot a szervernek.", "say.raw"))

    def handle_say_command(self, source, target, was_pm, args):
        message = " ".join(args)
        self.bot.send_message(target, message)

    def handle_say_to_command(self, source, target, was_pm, args):
        target = args[0]
        message = " ".join(args[1:])
        self.bot.send_message(target, message)

    def handle_raw_command(self, source, target, was_pm, args):
        message = " ".join(args)
        message = message.encode("u8", "ignore").decode("unicode_escape")
        self.bot.send_raw_line(message)