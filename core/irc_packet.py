def parse_nick_list_entry(entry):
    special_chars = "~@&+"
    special = None

    for char in special_chars:
        if entry.startswith(char):
            special = char
            entry = entry[1:]
            break

    return special, entry

class IrcUserSource:
    def __init__(self, nick, ident, host):
        self.nick = nick
        self.ident = ident
        self.host = host

    # Decode source string (eg. nick!ident@host) into an object instance
    @staticmethod
    def from_source_string(source_string):
        if "!" not in source_string:
            return IrcUserSource(source_string, None, None)

        nick, rest  = source_string.split("!")
        ident, host = rest.split("@")
        return IrcUserSource(nick, ident, host)
    
    def to_source_string(self):
        return "%s!%s@%s" % (self.nick, self.ident, self.host)

class IrcPacket:
    def __init__(self, source, command, args):
        self.source = source
        self.command = command
        self.args = args

    # Decodes a line into an IrcPacket (eg: :nick!ident@host PRIVMSG #channel :something)
    @staticmethod
    def from_line(line):
        source = None
        split = line.split(" ")
        args = []
        last_arg = None

        # We have a source
        # Can be assumed to hold at least one entry
        if split[0].startswith(":"):
            source = split.pop(0)
            source = source[1:] # Skip over :

        # Pop off command (eg: PRIVMSG)
        command = split.pop(0)

        # Iterate over args
        for entry in split:
            # We have found a last arg previously, append
            if last_arg != None:
                last_arg.append(entry)
            # This one is the start of the last argument
            # Arguments following a ':' should always be treated as one big argument
            # see PRIVMSG's :some message here at the end
            elif entry.startswith(":"):
                entry = entry[1:]
                last_arg = [entry] # Is a list for easier string building
            # Just a normal argument (like NICK's newnick)
            else:
                args.append(entry)

        # If we found one, join and append the last arg entries on " "
        if last_arg != None:
            args.append(" ".join(last_arg))

        return IrcPacket(source, command, args)