import core.module
import core.command
import core.bot_instance
import core.irc_packet
import core.line_socket
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name, self.on_stop)
        self.db = self.read_module_data({
            # don't bind to anything reachable remotely, it can be used for resource exhaustion
            "ip": "127.0.0.1",
            "port": 1234,
            "tag_channels": {}
        })

        self.register_command(
            core.command.Command("add_tag", self.handle_add_tag_command, 2, "<tag> <channel>",
                                 "Adds a broadcast tag to the specified channel.", "broadcast.add_tag"))
        self.register_command(
            core.command.Command("del_tag", self.handle_del_tag_command, 2, "<tag> <channel>",
                                 "Deletes a broadcast tag from the specified channel.", "broadcast.del_tag"))
        self.register_command(
            core.command.Command("list_tags", self.handle_list_tags_command, 0, None,
                                 "Lists all broadcast tags."))

        self.clients = []

        self.accept_sock = socket(AF_INET, SOCK_STREAM)
        self.accept_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.accept_sock.bind((self.db["ip"], self.db["port"]))
        self.accept_sock.listen(5)

        self.recv_thread = Thread(target=self.recv_thread_main, daemon=True)
        self.recv_thread.start()

    def broadcast_message(self, tag, should_hl, message):
        print("[broadcast] %s (%d): %s" % (tag, should_hl, message))

        for entry_tag, channels in self.db["tag_channels"].items():
            if entry_tag != tag:
                continue

            for channel_name in channels:
                if channel_name not in self.bot.channels:
                    continue

                if should_hl:
                    users = self.bot.channels[channel_name].users
                    message = "%s: %s" % (", ".join(users), message)

                self.bot.send_message(channel_name, "[%s] %s" % (tag, message))

    def client_thread_main(self, ip, port, socket):
        self.clients.append(socket)

        try:
            while True:
                line = socket.read_line()

                if line is None:
                    break

                splt = line.split(" ")
                tag = splt.pop(0)
                should_hl = bool(int(splt.pop(0)))
                message = " ".join(splt)
                self.broadcast_message(tag, should_hl, message)
        except ConnectionResetError:
            print("[broadcast] client %s:%d: disconnecting client on RST" %
                  (ip, port))
        except OSError:
            print("[broadcast] client %s:%d: sock got closed" % (ip, port))
        except Exception as err:
            # XXX TODO backtrace
            print("[broadcast] client %s:%d disconnecting on error %s" %
                  (ip, port, str(err)))

        print("[broadcast] client %s:%d: removed" % (ip, port))
        self.clients.remove(socket)

    def recv_thread_main(self):
        try:
            while True:
                c, addr = self.accept_sock.accept()
                ip, port = addr
                print("[broadcast] client %s:%d: accepted" % (ip, port))
                thread = Thread(target=self.client_thread_main, args=(
                    ip, port, core.line_socket.LineSocket(c)), daemon=True)
                thread.start()
        except OSError:
            print("[broadcast] accept socket got closed")

    def on_stop(self):
        for client in self.clients:
            client.unwrap().close()

        self.accept_sock.close()

    def handle_add_tag_command(self, source, target, is_pm, args):
        tag = args[0]
        tag_channel = args[1]

        if tag not in self.db["tag_channels"]:
            self.db["tag_channels"][tag] = []

        if tag_channel in self.db["tag_channels"][tag]:
            return

        self.db["tag_channels"][tag].append(tag_channel)
        self.bot.send_message(target, "Added.")
        self.write_module_data(self.db)

    def handle_del_tag_command(self, source, target, is_pm, args):
        tag = args[0]
        tag_channel = args[1]

        if tag not in self.db["tag_channels"]:
            return

        if tag_channel not in self.db["tag_channels"][tag]:
            return

        self.db["tag_channels"][tag].remove(tag_channel)

        if len(self.db["tag_channels"][tag]) == 0:
            del self.db["tag_channels"][tag]

        self.bot.send_message(target, "Deleted.")
        self.write_module_data(self.db)

    def handle_list_tags_command(self, source, target, is_pm, args):
        message = []

        for tag, channel_names in self.db["tag_channels"].items():
            tmp = []

            for channel_name in channel_names:
                tmp.append(channel_name)

            message.append("%s - %s" % (tag, ", ".join(tmp)))

        final_message = ", ".join(message)
        self.bot.send_message(target, "List of tags: %s\n" % final_message)
