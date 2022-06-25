import core.module
import core.command
import core.bot_instance
import core.irc_packet
from re import match as re_match

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.db = self.read_module_data({
            "patterns": {} # Map of greeting: greetings
        })

        self.register_event("core.other_join", self.handle_join)
        self.register_command(
            core.command.Command("add_greeting", self.handle_add_greeting_command, 2, "<pattern> <greeting>",
                "Sets the greeting for the specified pattern.", "greet.add_greeting"))
        self.register_command(
            core.command.Command("list_greetings", self.handle_list_greetings_command, 0, None,
                "Lists all stored greetings."))
        self.register_command(
            core.command.Command("del_greeting", self.handle_del_greeting_command, 1, "<pattern>",
                "Deletes the specified greeting.", "greet.del_greeting"))

    def handle_join(self, user_source, channel, user):
        patterns = self.db["patterns"]

        for pattern, entry in patterns.items():
            if re_match(pattern, user_source.to_source_string()):
                self.bot.send_message(channel.name, "%s: %s" % (user_source.nick, entry))

    def handle_add_greeting_command(self, source, target, was_pm, args):
        pattern = args[0]
        greeting = " ".join(args[1:])
        self.db["patterns"][pattern] = greeting
        self.write_module_data(self.db)
        self.bot.send_message(target, "Greeting added.")

    def handle_list_greetings_command(self, source, target, was_pm, args):
        message = []

        for pattern, greeting in self.db["patterns"].items():
            message.append("%s - %s" % (pattern, greeting))

        self.bot.send_message(target, "Greetings:\n%s" % "\n".join(message))

    def handle_del_greeting_command(self, source, target, was_pm, args):
        pattern = args[0]

        if pattern not in self.db["patterns"]:
            self.bot.send_message(target, "No such regex pattern.")
            return

        del self.db["patterns"][pattern]
        self.write_module_data(self.db)
        self.bot.send_message(target, "Greeting deleted.")