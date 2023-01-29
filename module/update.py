import core.module
import core.command
import core.bot_instance
import core.irc_packet
from subprocess import Popen, PIPE


def try_pull():
    proc = Popen(["git", "pull"], encoding="u8",
                 errors="ignore", stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        return err

    return out


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("pull", self.handle_pull_command, 0, None,
                                 "Does a git pull.", "update.pull"))

    def handle_pull_command(self, source, target, is_pm, args):
        message = try_pull()
        self.bot.send_message(target, message)
