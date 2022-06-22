import core.irc_socket
import core.user
import core.command
import core.channel
import core.json_data
import core.module
import core.irc_packet
from threading import Thread
from sys import stderr, modules as sys_modules
from socket import SHUT_RDWR
from enum import Enum
from time import sleep
from hashlib import sha256
from re import match as re_match
from ssl import create_default_context as ssl_create_default_context, SSLContext, CERT_NONE
from socket import socket, AF_INET, SOCK_STREAM

class BotInstanceState(Enum):
    DISCONNECTED = 0
    AUTHING = 1
    CONNECTED = 2
    STOPPING = 3

ssl_default_context = ssl_create_default_context()

ssl_useless_context = SSLContext() 
ssl_useless_context.verify_mode = CERT_NONE
ssl_useless_context.check_hostname = False

class BotInstance:
    def __init__(self, nick, ident, real_name, host, port, use_ssl, verify_ssl, db_name, command_prefix,
        init_channels, debug_channel, module_names):

        # Config
        self.nick = nick
        self.ident = ident
        self.real_name = real_name
        self.command_prefix = command_prefix
        self.db_name = db_name
        self.host = host
        self.port = port
        self.debug_channel = debug_channel
        self.init_channels = init_channels

        # State
        if use_ssl:
            context = ssl_default_context if verify_ssl else ssl_useless_context
            sock_to_wrap = context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname = host)
        else:
            sock_to_wrap = None

        self.socket = core.irc_socket.IrcSocket(sock_to_wrap)

        self.my_user = core.user.User(self.nick, self.ident, None, self.real_name)
        self.users = {self.nick: self.my_user} # Map of user nick -> User obj
        self.channels = {} # Map of channel name -> Channel obj
        self.whois_callbacks = {} # Map of user nick -> callback array

        # Misc
        self.module_instances = {} # Map of module name -> ModuleMain instance
        self.packet_handlers = {
            "PING": self.handle_ping,
            "JOIN": self.handle_join,
            "PART": self.handle_part,
            "QUIT": self.handle_quit,
            "NICK": self.handle_nick_change,
            "001": self.handle_connected,
            "ERROR": self.handle_error,
            "353": self.handle_nick_list,
            "352": self.handle_who_response,
            "311": self.handle_whois_response,
            "465": self.handle_gline,
            "433": self.handle_nick_in_use,
            "PRIVMSG": self.handle_privmsg,
            "NOTICE": self.handle_notice
        }

        self.state = BotInstanceState.DISCONNECTED
        self.should_reconnect = True
        self.reconnect_wait_time = 30

        # Message queueing
        self.privmsg_thread = Thread(target = self.privmsg_thread_main, daemon = True)
        self.privmsg_queue = []

        for module_name in module_names:
            try:
                self.load_module(module_name)
            except Exception as err:
                stderr.write("Loading module '%s' failed: %s\n" % (module_name, err))

    def inject_module(self, module_name, constructor):
        assert(module_name not in self.module_instances)
        self.module_instances[module_name] = constructor(self, module_name)

    # Loads a module from the modules/ directory
    def load_module(self, module_name):
        if module_name in self.module_instances:
            return

        # Sanitize module name
        # Can still make stuff like CON, PRN, AUX, ...
        # but obviously this isn't something to be called via an untrusted source
        module_name = module_name.replace(".", "")
        module_name = module_name.replace("/", "")
        module_name = module_name.replace("\\", "")

        full_import_path = "module.%s" % module_name

        # Clear cache
        if full_import_path in sys_modules:
            del sys_modules[full_import_path]

        # Load module namespace
        __import__(full_import_path)
        # Get sub-namespace in which ModuleMain resides
        data = sys_modules[full_import_path]
        # Finally, insert instance to module_instances dict
        constructor = getattr(data, "ModuleMain")
        self.inject_module(module_name, constructor)

    def remove_module(self, module_name):
        if module_name not in self.module_instances:
            return

        module = self.module_instances[module_name]
        module.stop()
        del self.module_instances[module_name]
        del sys_modules["module.%s" % module_name]

    def emit_bot_event(self, name, *args):
        for _, module in self.module_instances.items():
            module.handle_bot_event(name, *args)

    def send_raw_line(self, line):
        return self.socket.send_raw_line(line)

    def privmsg_thread_main(self):
        while self.state != BotInstanceState.STOPPING:
            if len(self.privmsg_queue) > 0:
                channel_name, message = self.privmsg_queue.pop(0)
                self.send_raw_line("PRIVMSG %s :%s" % (channel_name, message))

            sleep(1)

        print("[bot_instance] stopping message queue thread")

    def send_message(self, target, message):
        max_len = 300 # XXX, should be based on server info instead

        for line in message.split("\n"):
            while len(line) > max_len:
                part = line[:max_len]
                self.privmsg_queue.append((target, part))
                line = line[max_len:]

            self.privmsg_queue.append((target, line))

    def add_user(self, user):
        self.emit_bot_event("user.new", user)
        self.users[user.nick] = user

    def delete_user(self, user):
        self.emit_bot_event("user.delete", user)
        del self.users[user.nick]
    
    def handle_ping(self, source, args):
        self.send_raw_line("PONG %s" % " ".join(args))

    def handle_join(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        nick = user_source.nick
        channel_name = args[0]

        if channel_name not in self.channels:
            self.channels[channel_name] = core.channel.Channel(channel_name)

        channel = self.channels[channel_name]

        # Check whether we are the ones who are joining a channel
        if nick == self.nick:
            self.send_raw_line("WHO %s" % channel_name)
            # Update ourselves and update the channellist
            user = self.my_user
            channel.add_user(nick)
            user.add_channel(channel)
            return

        # Otherwise, it has to be someone else
        # Create new entry for the user if they weren't previously known
        if nick not in self.users:
            user = core.user.User(nick, user_source.ident, user_source.host, None)
            self.add_user(user)
        else:
            user = self.users[nick]

        # Update user and update the channellist
        channel.add_user(nick)
        user.add_channel(channel)

        # Queue who check for nick
        self.send_raw_line("WHO %s" % nick)

    def handle_part(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        nick = user_source.nick
        channel_name = args[0]
        channel = self.channels[channel_name]
        user = self.users[nick]

        if nick == self.nick:
            # It was us who parted the channel
            to_delete = []

            # Remove the channel entry from all user entries
            for user in self.users.values():
                if channel_name not in user.channels:
                    continue

                user.remove_channel(channel_name)

                # No need for channel.remove_user since it's going to get destroyed later
                #channel.remove_user(user)

                # We are on no common channels after the part, remove user from the userlist
                if len(user.channels) == 0:
                    to_delete.append(user)

            for user in to_delete:
                self.delete_user(user)

            # Destroy the channel entry
            del self.channels[channel_name]
        else:
            # Someone else parted the channel
            user.remove_channel(channel_name)
            channel.remove_user(user.nick)

            # We are on no common channels after the part, remove user from the userlist
            if len(user.channels) == 0:
                self.delete_user(user)

    def handle_quit(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        nick = user_source.nick
        
        # We got disconnected
        if nick == self.nick:
            self.socket.close()
            return

        user = self.users[nick]

        # Remove user from channels
        for channel in user.channels.values():
            channel.remove_user(user.nick)

        # Destroy user
        self.delete_user(user)

    def handle_nick_change(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        old_nick = user_source.nick
        new_nick = args[0]

        if old_nick == self.nick:
            self.nick = new_nick
            return

        user = self.users[old_nick]
        user.nick = new_nick
        # Remove old nick from userlist
        del self.users[old_nick]
        # Sanity check: two people can't have the same nick
        assert(new_nick not in self.users)
        self.users[new_nick] = user

        for channel in user.channels.values():
            channel.handle_nick_change(old_nick, new_nick)

    def handle_error(self, source, args):
        self.reconnect_wait_time = 30

    def handle_gline(self, source, args):
        self.should_reconnect = False

    def handle_connected(self, source, args):
        self.state = BotInstanceState.CONNECTED

        for channel in self.init_channels:
            self.send_raw_line("JOIN %s" % channel)

    def handle_nick_list(self, source, args):
        channel_name = args[2]
        nick_list = args[3]
        channel = self.channels[channel_name]

        for entry in nick_list.split(" "):
            _, nick = core.irc_packet.parse_nick_list_entry(entry)
            # TODO handle channel privileges

            if nick not in self.users:
                user = core.user.User(nick, None, None, None)
                self.add_user(user)
            else:
                user = self.users[nick]

            channel.add_user(nick)
            user.add_channel(channel)

    def handle_who_response(self, source, args):
        nick = args[5]

        # No need to process further
        if nick not in self.users:
            return

        user = self.users[nick]
        ident = args[2]
        host = args[3]
        real_name = args[7]

        # real_name part needs more processing (it's '0 actual realname' or something similar by default)
        real_name = real_name.split(" ")[1:]
        real_name = " ".join(real_name)

        if user.ident is None:
            user.ident = ident

        if user.host is None:
            user.host = host

        if user.real_name is None:
            user.real_name = real_name

    def queue_whois_lookup(self, nick, callback):
        if nick not in self.whois_callbacks:
            self.whois_callbacks[nick] = []
            self.send_raw_line("WHOIS %s" % nick)

        self.whois_callbacks[nick].append(callback)

    def handle_whois_response(self, source, args):
        nick = args[1]

        # Disgusting blocking garbage
        response_list = self.socket.read_irc_packets_until("318")
        authed_as = None

        assert(response_list is not None)

        for packet in response_list:
            self.handle_packet(packet)

            if packet.command == "330":
                authed_as = packet.args[2]
                break

        # Run callbacks
        if nick in self.whois_callbacks:
            for callback in self.whois_callbacks[nick]:
                callback(authed_as)

            del self.whois_callbacks[nick]

    def get_account_data(self, account_name):
        account_defaults = {
            "name": account_name,
            "is_admin": False,
            "acl_rights": []
        }

        hashed = sha256(account_name.encode("u8", "ignore")).hexdigest()
        result = core.json_data.read_json_data(account_defaults,
            "data", self.db_name, "accounts", "%s.json" % hashed)

        # Imagine finding an sha256 collision here
        assert(result["name"] == account_name)
        return result
    
    def check_admin_from_host(self, mask):
        defaults = {
            "masks": []
        }

        results = core.json_data.read_json_data(defaults, "data", self.db_name, "admin_masks.json")

        for stored_mask in results["masks"]:
            if re_match(stored_mask, mask):
                return True

        return False
    
    def run_command(self, command, source, reply_target, is_pm, args):
        if len(args) < command.min_args:
            self.send_message(reply_target, self.command_prefix + command.format_help())
            return

        # If no whois lookup is needed, the command can be executed immediately
        if command.acl_key is None:
            command.execute(source, reply_target, is_pm, args)
            return

        # For networks like IRCNet / EFNet
        if self.check_admin_from_host("%s!%s@%s" % (source.nick, source.ident, source.host)):
            command.execute(source, reply_target, is_pm, args)
            return

        def account_ready(authed_as):
            if authed_as is None:
                self.send_message(reply_target, "You need to log in to use the '%s' command." % command.name)
                return

            account = self.get_account_data(authed_as)

            if not account["is_admin"] and command.acl_key not in account["acl_rights"]:
                self.send_message(reply_target, "You have no permission to use the '%s' command." % command.name)
                return

            try:
                command.execute(source, reply_target, is_pm, args)
            except Exception as err:
                self.write_exception("Error processing privileged command %s" % (self.command_prefix + command.name), err)

        # Queue an account lookup
        self.queue_whois_lookup(source.nick, account_ready)

    def try_process_command(self, source, reply_target, message, is_pm):
        # Early return if we don't support commands at all
        if self.command_prefix is None:
            return

        # Early return if it's not a command
        if not message.startswith(self.command_prefix):
            return
        
        # Command handling
        message = message[len(self.command_prefix):]
        args = message.split(" ")

        if len(args) == 0:
            return

        command_name = args.pop(0)

        # Look up and run command in modules
        for module in self.module_instances.values():
            if command_name not in module.commands:
                continue

            command = module.commands[command_name]

            try:
                self.run_command(command, source, reply_target, is_pm, args)
            except Exception as err:
                self.write_exception("Error processing command %s" % (self.command_prefix + command.name), err)

    def handle_privmsg(self, source, args):
        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        channel_name = args[0]
        message = args[1]
        is_pm = channel_name == self.nick
        reply_target = user_source.nick if is_pm else channel_name

        self.emit_bot_event("message", user_source, reply_target, is_pm, message)
        self.try_process_command(user_source, reply_target, message, is_pm)

    def handle_notice(self, source, args):
        channel_name = args[0]
        message = args[1]

        if "!" not in source:
            self.emit_bot_event("server_notice", source, channel_name, message)
            return

        user_source = core.irc_packet.IrcUserSource.from_source_string(source)
        is_pm = channel_name == self.nick
        reply_target = user_source.nick if is_pm else channel_name
        self.emit_bot_event("notice", user_source, reply_target, is_pm, message)

    def handle_nick_in_use(self, source, args):
        if self.state != BotInstanceState.AUTHING:
            return

        self.nick += "_"
        self.send_raw_line("NICK %s" % self.nick)

    def write_exception(self, prefix, exception):
        if self.debug_channel is None:
            return

        try:
            self.send_message(self.debug_channel, "%s: %s %s" % (prefix, type(exception).__name__, exception))
        except Exception as err:
            pass

    # Top-level packet handling dispatch function
    def handle_packet(self, packet):
        print(packet.source, packet.command, " ".join(packet.args))

        try:
            if packet.command in self.packet_handlers:
                self.packet_handlers[packet.command](packet.source, packet.args)
        except Exception as err:
            self.write_exception("Error processing %s packet in global" % packet.command, err)

        # Handle packet events in modules
        for mod_name, mod_instance in self.module_instances.items():
            try:
                mod_instance.handle_packet(packet)
            except Exception as err:
                self.write_exception("Error processing %s packet in module %s" % (packet.command, mod_name), err)

    def run(self):
        self.privmsg_thread.start()

        try:
            # Connect and auth
            self.socket.connect((self.host, self.port))
            self.state = BotInstanceState.AUTHING
            self.send_raw_line("NICK %s" % self.nick)
            self.send_raw_line("USER %s 0 * :%s" % (self.ident, self.real_name))

            # Main read loop
            while True:
                packet = self.socket.read_irc_packet()

                # We got disconnected
                if packet is None:
                    break

                self.handle_packet(packet)

        except ConnectionResetError:
            print("[bot_instance] bot got disconnected")

        except OSError:
            print("[bot_instance] bot socket got closed")

        for module in self.module_instances.values():
            module.stop()

        self.state = BotInstanceState.STOPPING
        self.privmsg_thread.join()

    def disconnect(self):
        try:
            self.socket.shutdown(SHUT_RDWR)
        except OSError:
            pass

        self.socket.close()
        self.should_reconnect = False

    def restart(self):
        try:
            self.socket.shutdown(SHUT_RDWR)
        except OSError:
            pass

        self.socket.close()
        self.reconnect_wait_time = 0