import core.module
import core.command
import core.bot_instance
import core.irc_packet
from subprocess import Popen, PIPE


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("quit", self.handle_quit_command, 0, "(<reason...>)",
                                 "QUITs the current server.", "network.quit"))
        self.register_command(
            core.command.Command("restart", self.handle_restart_command, 0, "(<reason...>)",
                                 "Restarts the bot.", "network.restart"))

    def handle_quit_command(self, source, target, is_pm, args):
        reason = " ".join(args)

        if len(reason) > 0:
            self.bot.send_immediately("QUIT :%s" % reason)
        else:
            self.bot.send_immediately("QUIT")

        self.bot.disconnect()

    def handle_restart_command(self, source, target, is_pm, args):
        reason = " ".join(args)

        if len(reason) > 0:
            self.bot.send_immediately("QUIT :%s" % reason)
        else:
            self.bot.send_immediately("QUIT")

        self.bot.restart()
