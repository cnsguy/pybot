import core.module
import core.command
import core.bot_instance
import core.irc_packet
from re import match as re_match

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.config = self.read_module_config({
            "patterns": {} # Map of greeting: greetings
        })

        self.register_packet_handler("JOIN", self.handle_join)
        self.register_command(
            core.command.Command("add_greeting", self.handle_add_greeting_command, 2, "<pattern> <greeting>",
                "Sets the greeting for the specified pattern.", "greet.add_greeting"))
        self.register_command(
            core.command.Command("list_greetings", self.handle_list_greetings_command, 0, None,
                "Lists all stored greetings."))
        self.register_command(
            core.command.Command("del_greeting", self.handle_del_greeting_command, 1, "<pattern>",
                "Deletes the specified greeting.", "greet.del_greeting"))

    def handle_join(self, source, args):
        channel_name = args[0]
        patterns = self.config["patterns"]
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)

        for pattern, entry in patterns.items():
            if re_match(pattern, source):
                self.bot.send_message(channel_name, "%s: %s" % (user_source.nick, entry))

    def handle_add_greeting_command(self, source, target, was_pm, args):
        pattern = args[0]
        greeting = " ".join(args[1:])

        self.config["patterns"][pattern] = greeting
        self.write_module_config(self.config)
        self.bot.send_message(target, "Greeting added.")

    def handle_list_greetings_command(self, source, target, was_pm, args):
        message = []

        for pattern, greeting in self.config["patterns"].items():
            message.append("%s - %s" % (pattern, greeting))

        self.bot.send_message(target, "Greetings:\n%s" % "\n".join(message))

    def handle_del_greeting_command(self, source, target, was_pm, args):
        pattern = args[0]

        if pattern not in self.config["patterns"]:
            self.bot.send_message(target, "No such regex pattern.")
            return

        del self.config["patterns"][pattern]
        self.write_module_config(self.config)
        self.bot.send_message(target, "Greeting deleted.")