import core.module
import core.command
import core.bot_instance
import core.irc_packet
from random import choice
from re import match as re_match


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.db = self.read_module_data({
            "ignored": [],
            "messages": []
        })

        self.register_event("core.message", self.handle_message)
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

        if len(message) > 0 and message not in self.db["messages"]:
            self.db["messages"].append(message)
            self.write_module_data(self.db)

        return choice(self.db["messages"])

    def handle_message(self, user_source, reply_target, is_pm, message):
        if is_pm:
            return

        if not message.startswith(self.bot.nick + ":"):
            return

        for pattern in self.db["ignored"]:
            if re_match(pattern, user_source.to_source_string()):
                return

        self.bot.send_message(reply_target, self.run_talk(message))

    def handle_add_ignore_command(self, source, target, is_pm, args):
        pattern = args[0]

        if pattern in self.db["ignored"]:
            self.bot.send_message(target, "Already ignored.")
            return

        self.db["ignored"].append(pattern)
        self.write_module_data(self.db)
        self.bot.send_message(target, "Ignored.")

    def handle_list_ignores_command(self, source, target, is_pm, args):
        message = []

        for pattern in self.db["ignored"]:
            message.append(pattern)

        final_message = "List of ignores:\n%s" % "\n".join(message)
        self.bot.send_message(target, final_message)

    def handle_del_ignore_command(self, source, target, is_pm, args):
        pattern = args[0]

        if pattern not in self.db["ignored"]:
            self.bot.send_message(target, "No such pattern.")
            return

        self.db["ignored"].remove(pattern)
        self.write_module_data(self.db)
        self.bot.send_message(target, "Unignored.")
