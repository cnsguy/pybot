import core.module
import core.command
import core.bot_instance
import core.irc_packet
from random import choice
from re import match as re_match

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.config = self.read_module_config({
            "ignored": [],
            "messages": []
        })

        self.register_packet_handler("PRIVMSG", self.handle_privmsg)
        self.register_command(
            core.command.Command("talk_ignore", self.handle_add_ignore_command, 1, "<pattern>",
                "<pattern>", "talk.add_ignore"))
        self.register_command(
            core.command.Command("list_ignores", self.handle_list_ignores_command, 0, None,
                None))
        self.register_command(
            core.command.Command("talk_unignore", self.handle_del_ignore_command, 1, "<pattern>",
                "<pattern>", "talk.del_ignore"))

    def run_talk(self, message):
        message = ":".join(message.split(":")[1:]).strip()

        if len(message) > 0 and message not in self.config["messages"]:
            self.config["messages"].append(message)
            self.write_module_config(self.config)

        return choice(self.config["messages"])

    def handle_privmsg(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        target = user_source.nick if args[0] == self.bot.nick else args[0]
        message = args[1]

        if not message.startswith(self.bot.nick + ":"):
            return

        for pattern in self.config["ignored"]:
            if re_match(pattern, source):
                return

        self.bot.send_message(target, self.run_talk(message))

    def handle_add_ignore_command(self, source, target, was_pm, args):
        pattern = args[0]

        if pattern in self.config["ignored"]:
            self.bot.send_message(target, "Already ignored.")
            return

        self.config["ignored"].append(pattern)
        self.write_module_config(self.config)
        self.bot.send_message(target, "Ignored.")

    def handle_list_ignores_command(self, source, target, was_pm, args):
        message = []

        for pattern in self.config["ignored"]:
            message.append(pattern)

        final_message = "List of ignores:\n%s" % "\n".join(message)
        self.bot.send_message(target, final_message)

    def handle_del_ignore_command(self, source, target, was_pm, args):
        pattern = args[0]

        if pattern not in self.config["ignored"]:
            self.bot.send_message(target, "No such pattern.")
            return

        self.config["ignored"].remove(pattern)
        self.write_module_config(self.config)
        self.bot.send_message(target, "Unignored.")