import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("quit", self.handle_quit_command, 0, "(<indok...>)",
                "Kilep a jelenlegi irc szerverrol", "network.quit"))
        self.register_command(
            core.command.Command("restart", self.handle_restart_command, 0, "(<indok...>)",
                "Ujrainditja a botot", "network.restart"))

    def handle_quit_command(self, source, target, was_pm, args):
        reason = " ".join(args)

        if len(reason) > 0:
            self.bot.send_raw_line("QUIT :%s" % reason)
        else:
            self.bot.send_raw_line("QUIT")

        self.bot.disconnect()

    def handle_restart_command(self, source, target, was_pm, args):
        reason = " ".join(args)

        if len(reason) > 0:
            self.bot.send_raw_line("QUIT :%s" % reason)
        else:
            self.bot.send_raw_line("QUIT")

        self.bot.restart()