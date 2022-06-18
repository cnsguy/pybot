import core.irc_packet
import core.line_socket

class IrcSocket(core.line_socket.LineSocket):
    def __init__(self, wrap = None):
        super().__init__(wrap)

    # Reads and decodes a single IrcPacket from the server
    # NOTE: This blocks until enough data is available
    # NOTE: This will return None if we are disconnected
    def read_irc_packet(self):
        result = self.read_line()

        if result is None:
            return result

        return core.irc_packet.IrcPacket.from_line(result)

    # Reads irc packets until a given command field is encountered
    # Useful for stuff like WHOIS response handling
    def read_irc_packets_until(self, command):
        results = []

        while True:
            result = self.read_irc_packet()

            # Forward disconnect notification
            if result == None:
                return result

            results.append(result)

            if result.command == command:
                break

        return results