class Channel:
    def __init__(self, name):
        self.name = name
        self.users = set()

    def add_user(self, nick):
        self.users.add(nick)

    def remove_user(self, nick):
        self.users.remove(nick)

    def handle_nick_change(self, old_nick, new_nick):
        self.remove_user(old_nick)
        self.add_user(new_nick)
