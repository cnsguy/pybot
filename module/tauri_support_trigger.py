import core.module
import core.command
import core.bot_instance
import core.irc_packet
from re import match as re_match, sub as re_sub, finditer as re_finditer
from datetime import datetime
from time import time


def escape_nick(nick):
    return nick[0] + "." + nick[1:]


class SupportEntry:
    def __init__(self, start_hour, end_hour, nick, languages):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.nick = nick
        self.languages = languages

    def format_line(self):
        return "%d:00-%d:00 CET %s (%s)" % (self.start_hour, self.end_hour, escape_nick(self.nick), ", ".join(self.languages))


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)

        self.db = self.read_module_data({
            "patterns": []
        })

        self.support_entries = [
            SupportEntry(16, 24, "Oxym", ["English", "Magyar"]),
            SupportEntry(14, 21, "Mokeszli", ["Magyar"]),
        ]

        self.register_command(
            core.command.Command("support_trigger_add", self.handle_add_command, 1, "<pattern...>",
                                 "Adds a new support trigger pattern.", "support_trigger.support_trigger_add"))
        self.register_command(
            core.command.Command("support_trigger_del", self.handle_del_command, 1, "<pattern...>",
                                 "Deletes a support trigger pattern.", "support_trigger.support_trigger_del"))
        self.register_command(
            core.command.Command("support_trigger_list", self.handle_list_command, 0, None,
                                 "Lists current support trigger patterns."))
        self.register_command(
            core.command.Command("support", self.handle_support_command, 0, None,
                                 "Manual support message trigger."))

        self.users_already_informed = set()
        self.register_event("user.delete", self.drop_informed_entry)
        self.register_event("core.message", self.handle_message)

    def drop_informed_entry(self, user):
        if user not in self.users_already_informed:
            return

        self.users_already_informed.remove(user)

    def send_message(self, target):
        available = self.collect_available()
        unavailable = [x for x in self.support_entries if x not in available]
        self.bot.send_message(
            target, "Support is available on workdays | Munkanapokon van support.")

        if len(available) > 0:
            self.bot.send_message(
                target, "Currently available support staff | Jelenleg elérhető:")

            for entry in available:
                self.bot.send_message(target, entry.format_line())

        if len(unavailable) > 0:
            self.bot.send_message(
                target, "Currently unavailable support staff | Jelenleg nem elérhető:")

            for entry in unavailable:
                self.bot.send_message(target, entry.format_line())

    def collect_available(self):
        results = []
        info = datetime.now()

        if info.weekday() >= 5:  # checks for weekends (0-based)
            return []

        for entry in self.support_entries:
            if info.hour >= entry.start_hour and info.hour <= entry.end_hour - 1:
                results.append(entry)

        return results

    def support_matched(self, user, target):
        self.send_message(target)
        self.users_already_informed.add(user)

    def handle_message(self, user_source, reply_target, is_pm, message):
        if is_pm:
            return

        user = self.bot.users.get(user_source.nick, None)

        if user is None or user in self.users_already_informed:
            return

        for entry in self.db["patterns"]:
            if re_match(entry, message.lower()):
                self.support_matched(user, reply_target)
                return

    def handle_add_command(self, source, target, is_pm, args):
        pattern = " ".join(args[0:])

        if pattern in self.db["patterns"]:
            self.bot.send_message(target, "Pattern already exists.")
            return

        self.db["patterns"].append(pattern)
        self.write_module_data(self.db)
        self.bot.send_message(target, "Pattern added.")

    def handle_del_command(self, source, target, is_pm, args):
        pattern = " ".join(args[0:])

        try:
            idx = self.db["patterns"].index(pattern)
        except ValueError:
            self.bot.send_message(target, "No such pattern.")
            return

        del self.db["patterns"][idx]
        self.write_module_data(self.db)
        self.bot.send_message(target, "Pattern deleted.")

    def handle_list_command(self, source, target, is_pm, args):
        message = []

        for entry in self.db["patterns"]:
            message.append("%s" % entry)

        self.bot.send_message(target, "Triggers:\n%s" % "\n".join(message))

    def handle_support_command(self, source, target, is_pm, args):
        self.send_message(target)
