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
        self.register_bot_event("message", self.handle_message)
        self.register_packet_handler("PART", self.handle_part)

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

    def handle_part(self, source, args):
        channel_name = args[0]
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        user = self.bot.users[user_source.nick]

        if channel_name not in self.message_backlog:
            return

        self.message_backlog[channel_name].flush_user(user)
    
    def handle_sed_command(self, source, target, was_pm, args):
        if was_pm:
            self.bot.send_message(target, "PMben minek?")
            return

        if target not in self.message_backlog:
            self.bot.send_message(target, "Ide meg senki sem irt semmit.")
            return
        
        channel_backlog = self.message_backlog[target]
        user = self.bot.users[source.nick]
        user_backlog = channel_backlog.get_user_backlog(user)

        if user_backlog is None:
            self.bot.send_message(target, "Nem is irtal meg semmit..")
            return

        if args[0].startswith("-"):
            try:
                offset = int(args[0])
            except ValueError:
                self.bot.send_message(target, "Ezt a szamot nem ismerem")
                return
            
            args.pop(0)
        else:
            offset = -1

        result = parse_sed(" ".join(args))

        if result is None:
            self.bot.send_message(target, "Te mit tesa?")
            return

        if abs(offset) > len(user_backlog):
            self.bot.send_message(target, "Jo nagy offset, de nem")
            return

        pattern, replacement, count = result
        message = user_backlog[offset]
        result = re_sub(pattern, replacement, message, count = count)
        result = "%s erre gondolt: %s" % (user.nick, result)
        self.bot.send_message(target, result)

    def handle_gsed_command(self, source, target, was_pm, args):
        if was_pm:
            self.bot.send_message(target, "PMben minek?")
            return

        if target not in self.message_backlog:
            self.bot.send_message(target, "Ide meg senki sem irt semmit.")
            return

        channel_backlog = self.message_backlog[target].get_backlog()

        if args[0].startswith("-"):
            try:
                offset = int(args[0])
            except ValueError:
                self.bot.send_message(target, "Ezt a szamot nem ismerem")
                return
            
            args.pop(0)
        else:
            offset = -1

        if abs(offset) > len(channel_backlog):
            self.bot.send_message(target, "Jo nagy offset, de nem")
            return

        result = parse_sed(" ".join(args))

        if result is None:
            self.bot.send_message(target, "Te mit tesa?")
            return

        pattern, replacement, count = result
        orig_nick, message = channel_backlog[offset]
        result = re_sub(pattern, replacement, message, count = count)
        result = "%s szerint %s erre gondolt: %s" % (source.nick, orig_nick, result)
        self.bot.send_message(target, result)