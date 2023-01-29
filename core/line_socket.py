from socket import socket, AF_INET, SOCK_STREAM

# Tries to decode the line as utf8, then latin2, then finally utf8 with ignore if neither worked


def decode_line_to_string(line):
    try:
        return line.decode("u8")
    except UnicodeDecodeError:
        pass  # Dont want to nest them

    try:
        return line.decode("iso-8859-2")
    except Exception:  # XXX change this
        pass

    return line.decode("u8", "ignore")


class LineSocket:
    def __init__(self, wrap=None, max_buffer_size=8192):
        if wrap is None:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = wrap

        self.line_buffer = bytearray()
        self.max_buffer_size = max_buffer_size

    def unwrap(self):
        return self.sock

    # Ask for a (host: str, port: int) tuple for consistency with normal socket's .connect()
    def connect(self, host_port_tuple):
        self.sock.connect(host_port_tuple)

    def close(self):
        self.sock.close()

    def shutdown(self, how):
        self.sock.shutdown(how)

    # Reads and decodes a single line
    # NOTE: This blocks until enough data is available
    # NOTE: This will return None if we are disconnected
    def read_line(self):
        while True:
            line_idx = self.line_buffer.find(b"\n")

            # If it's not -1 / found in the string, then decode and return with the packet we just completed
            if line_idx != -1:
                # Slice off and decode the line
                line = self.line_buffer[:line_idx]
                decoded_line = decode_line_to_string(line)

                # Slice off the \r from the decoded line
                if decoded_line.endswith("\r"):
                    decoded_line = decoded_line[:-1]

                # Move the buffer over the stuff we just popped off (+1 because of skipping over \n)
                self.line_buffer = self.line_buffer[line_idx + 1:]

                # Done
                return decoded_line

            recv_result = self.sock.recv(512)

            # Signal disconnect to caller side if socket gets disconnected
            if len(recv_result) == 0:
                self.close()
                return None

            self.line_buffer += recv_result

            # checking this late should be fine
            if len(self.line_buffer) > self.max_buffer_size:
                self.close()
                return None

    # Sends a raw line (string)
    def send_raw_line(self, line):
        # XXX make encoding configurable
        encoded_line = line.encode("u8", "ignore")
        self.sock.send(encoded_line + b"\r\n")


class SSLLineSocket(LineSocket):
    def __init__(self, wrap=None, max_buffer_size=8192):
        pass
