class User:
    def __init__(self, nick, ident, host, real_name):
        self.nick = nick
        self.ident = ident
        self.host = host
        self.real_name = real_name
        self.channels = {}

    def add_channel(self, channel):
        self.channels[channel.name] = channel

    def remove_channel(self, channel_name):
        del self.channels[channel_name]