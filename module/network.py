import core.module
import core.command
import core.bot_instance
import core.irc_packet
from subprocess import Popen, PIPE

def get_latest_commit(repo):
    proc = Popen(["git", "log", repo, "main", "--oneline", "--no-color"], stdout = PIPE, encoding = "u8")
    out, _ = proc.communicate()
    out = out.split("\n")
    return out[0].strip()

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("quit", self.handle_quit_command, 0, "(<reason...>)",
                "QUITs the current server.", "network.quit"))
        self.register_command(
            core.command.Command("restart", self.handle_restart_command, 0, "(<reason...>)",
                "Restarts the bot.", "network.restart"))
        self.register_command(
            core.command.Command("update", self.handle_update_command, 0, None,
                "Checks git origin/main for updates and restarts the bot if there are any.", "network.update"))

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

    def handle_update_command(self, source, target, is_pm, args):
        proc = Popen(["git", "fetch", "origin"])
        proc.communicate()
        last_local = get_latest_commit("main")
        last_remote = get_latest_commit("origin/main")

        if last_remote == last_local:
            self.bot.send_message(target, "No new commits on origin/main.")
            return

        self.bot.send_immediately("QUIT :Updating to %s" % last_remote)
        self.bot.restart()