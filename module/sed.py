import core.module
import core.command
import core.bot_instance
import core.irc_packet
import core.user
import core.channel
from collections import deque
from re import sub as re_sub

class ChannelBacklog:
    def __init__(self):
        self.messages = deque(maxlen = 10)
        self.user_messages = {}

    def add_message(self, user, message):
        self.messages.append((user.nick, message))

        if not user in self.user_messages:
            self.user_messages[user] = deque(maxlen = 10)

        self.user_messages[user].append(message)

    def flush_user(self, user):
        if user in self.user_messages:
            del self.user_messages[user]

    def get_user_backlog(self, user):
        return self.user_messages.get(user)
    
    def get_backlog(self):
        return self.messages

def parse_sed(command):
    if not command.startswith("s") or len(command) < 2:
        return None

    command = command[1:]
    command_args = command[1:].split(command[0])

    if len(command_args) < 2 or len(command_args) > 3:
        return None

    pattern = command_args[0]
    replacement = command_args[1]
    count = 1

    if len(command_args) == 3 and len(command_args[2]) > 0:
        if command_args[2] != "g":
            return None

        count = 0

    return pattern, replacement, count

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.message_backlog = {}
        self.channel_message_backlog = {}
        self.register_command(
            core.command.Command("sed", self.handle_sed_command, 1, "<pattern>",
                "Sed."))
        self.register_command(
            core.command.Command("gsed", self.handle_gsed_command, 1, "<pattern>",
                "Global sed."))
        self.register_event("core.message", self.handle_message)
        self.register_event("core.self_part", self.handle_self_part)
        self.register_event("core.other_part", self.handle_other_part)

    def handle_message(self, source, reply_target, was_pm, message):
        if was_pm or message.startswith(self.bot.command_prefix):
            return

        # TODO handle s// stuff
        if message.startswith("s/"):
            self.handle_sed_command(source, reply_target, False, message.split(" "))
            return

        channel_name = reply_target
        user = self.bot.users[source.nick]

        if channel_name not in self.message_backlog:
            self.message_backlog[channel_name] = ChannelBacklog()

        self.message_backlog[channel_name].add_message(user, message)

    def handle_self_part(self, user_source, channel, user):
        del self.message_backlog[channel.name]

    def handle_other_part(self, user_source, channel, user):
        user = self.bot.users[user.nick]

        if channel.name not in self.message_backlog:
            return

        self.message_backlog[channel.name].flush_user(user)
    
    def handle_sed_command(self, source, target, was_pm, args):
        if was_pm:
            self.bot.send_message(target, "Why would you use sed in this PM...?")
            return

        if target not in self.message_backlog:
            self.bot.send_message(target, "No messages in backlog yet. (Backlog is in-memory only)")
            return
        
        channel_backlog = self.message_backlog[target]
        user = self.bot.users[source.nick]
        user_backlog = channel_backlog.get_user_backlog(user)

        if user_backlog is None:
            self.bot.send_message(target, "No messages in your personal backlog yet.")
            return

        if args[0].startswith("-"):
            try:
                offset = int(args[0])
            except ValueError:
                self.bot.send_message(target, "Cannot parse number.")
                return
            
            args.pop(0)
        else:
            offset = -1

        result = parse_sed(" ".join(args))

        if result is None:
            self.bot.send_message(target, "Cannot parse sed expression.")
            return

        if abs(offset) > len(user_backlog):
            self.bot.send_message(target, "Offset larger than the size of backlog.")
            return

        pattern, replacement, count = result
        message = user_backlog[offset]
        result = re_sub(pattern, replacement, message, count = count)
        result = "%s meant: %s" % (user.nick, result)
        self.bot.send_message(target, result)

    def handle_gsed_command(self, source, target, was_pm, args):
        if was_pm:
            self.bot.send_message(target, "Why would you use sed in this PM...?")
            return

        if target not in self.message_backlog:
            self.bot.send_message(target, "No messages in backlog yet. (Backlog is in-memory only)")
            return

        channel_backlog = self.message_backlog[target].get_backlog()

        if args[0].startswith("-"):
            try:
                offset = int(args[0])
            except ValueError:
                self.bot.send_message(target, "Cannot parse number.")
                return
            
            args.pop(0)
        else:
            offset = -1

        if abs(offset) > len(channel_backlog):
            self.bot.send_message(target, "Offset larger than the size of backlog.")
            return

        result = parse_sed(" ".join(args))

        if result is None:
            self.bot.send_message(target, "Cannot parse sed expression.")
            return

        pattern, replacement, count = result
        orig_nick, message = channel_backlog[offset]
        result = re_sub(pattern, replacement, message, count = count)
        result = "%s thinks %s meant: %s" % (source.nick, orig_nick, result)
        self.bot.send_message(target, result)