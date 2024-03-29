import core.module
import core.command
import core.bot_instance
import core.irc_packet
from re import match as re_match, sub as re_sub, finditer as re_finditer


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.db = self.read_module_data({
            "patterns": []
        })

        self.register_event("core.message", self.handle_message)
        self.register_command(
            core.command.Command("word_trigger_add", self.handle_add_command, 2, "<sender_pattern> <word_pattern> <response>",
                                 "Adds a new word trigger pattern.", "word_trigger.word_trigger_add"))
        self.register_command(
            core.command.Command("word_trigger_del", self.handle_del_command, 2, "<sender_pattern> <word_pattern> <response>",
                                 "Deletes a word trigger pattern.", "word_trigger.word_trigger_del"))
        self.register_command(
            core.command.Command("word_trigger_list", self.handle_list_command, 0, None,
                                 "Lists current word trigger patterns."))

    def handle_message(self, user_source, reply_target, is_pm, message):
        if is_pm:
            return

        for entry in self.db["patterns"]:
            if re_match(entry["sender_pattern"], user_source.to_source_string()):
                for match in re_finditer(entry["word_pattern"], message):
                    start, end = match.span()
                    self.bot.send_message(reply_target, re_sub(
                        entry["word_pattern"], entry["response"], message[start:end]))

    def handle_add_command(self, source, target, is_pm, args):
        sender_pattern = args[0]
        word_pattern = args[1]
        response = " ".join(args[2:])
        saved_object = {
            "sender_pattern": sender_pattern,
            "word_pattern": word_pattern,
            "response": response
        }

        if saved_object in self.db["patterns"]:
            self.bot.send_message(target, "Pattern already exists.")
            return

        self.db["patterns"].append(saved_object)
        self.write_module_data(self.db)
        self.bot.send_message(target, "Pattern added.")

    def handle_del_command(self, source, target, is_pm, args):
        sender_pattern = args[0]
        word_pattern = args[1]
        response = " ".join(args[2:])
        saved_object = {
            "sender_pattern": sender_pattern,
            "word_pattern": word_pattern,
            "response": response
        }

        try:
            idx = self.db["patterns"].index(saved_object)
        except ValueError:
            self.bot.send_message(target, "No such pattern.")
            return

        del self.db["patterns"][idx]
        self.write_module_data(self.db)
        self.bot.send_message(target, "Pattern deleted.")

    def handle_list_command(self, source, target, is_pm, args):
        message = []

        for entry in self.db["patterns"]:
            message.append("%s %s %s" % (
                entry["sender_pattern"], entry["word_pattern"], entry["response"]))

        self.bot.send_message(target, "Triggers:\n%s" % "\n".join(message))
