import core.module
import core.command
import core.bot_instance
import core.irc_packet
from re import match as re_match, sub as re_sub, finditer as re_finditer

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.config = self.read_module_config({
            "patterns": []
        })

        self.register_packet_handler("PRIVMSG", self.handle_privmsg)
        self.register_command(
            core.command.Command("word_trigger_add", self.handle_add_command, 2, "<sender_pattern> <word_pattern> <response>",
                "Adds a new word trigger pattern.", "word_trigger.word_trigger_add"))
        self.register_command(
            core.command.Command("word_trigger_del", self.handle_del_command, 2, "<sender_pattern> <word_pattern> <response>",
                "Deletes a word trigger pattern.", "word_trigger.word_trigger_del"))
        self.register_command(
            core.command.Command("word_trigger_list", self.handle_list_command, 0, None,
                "Lists current word trigger patterns."))

    def handle_privmsg(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        target = user_source.nick if args[0] == self.bot.nick else args[0]
        message = args[1]

        for entry in self.config["patterns"]:
            if re_match(entry["sender_pattern"], source):
                for match in re_finditer(entry["word_pattern"], message):
                    start, end = match.span()
                    self.bot.send_message(target, re_sub(entry["word_pattern"], entry["response"], message[start:end]))

    def handle_add_command(self, source, target, was_pm, args):
        sender_pattern = args[0]
        word_pattern = args[1]
        response = " ".join(args[2:])
        saved_object = {
            "sender_pattern": sender_pattern,
            "word_pattern": word_pattern,
            "response": response
        }

        if saved_object in self.config["patterns"]:
            self.bot.send_message(target, "Pattern already exists.")
            return

        self.config["patterns"].append(saved_object)
        self.write_module_config(self.config)
        self.bot.send_message(target, "Pattern added.")

    def handle_del_command(self, source, target, was_pm, args):
        sender_pattern = args[0]
        word_pattern = args[1]
        response = " ".join(args[2:])
        saved_object = {
            "sender_pattern": sender_pattern,
            "word_pattern": word_pattern,
            "response": response
        }

        try:
            idx = self.config["patterns"].index(saved_object)
        except ValueError:
            self.bot.send_message(target, "No such pattern.")
            return
        
        del self.config["patterns"][idx]
        self.write_module_config(self.config)
        self.bot.send_message(target, "Pattern deleted.")

    def handle_list_command(self, source, target, was_pm, args):
        message = []

        for entry in self.config["patterns"]:
            message.append("%s %s %s" % (entry["sender_pattern"], entry["word_pattern"], entry["response"]))

        self.bot.send_message(target, "Triggers:\n%s" % "\n".join(message))