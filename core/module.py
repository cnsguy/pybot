import core.json_data


class Module:
    def __init__(self, bot, name, stop_handler=None):
        self.bot = bot
        self.name = name
        self.event_handlers = {}
        self.commands = {}
        self.stop_handler = stop_handler

    def register_command(self, command):
        self.commands[command.name] = command

    def register_event(self, name, fn):
        self.event_handlers[name] = fn

    def read_module_data(self, defaults):
        return core.json_data.read_json_data(defaults, "data", self.bot.db_name, "module", "%s.json" % self.name)

    def write_module_data(self, values):
        return core.json_data.write_json_data(values, "data", self.bot.db_name, "module", "%s.json" % self.name)

    def handle_event(self, name, *args):
        if name in self.event_handlers:
            self.event_handlers[name](*args)

    # Used in BotInstance.module_remove
    def stop(self):
        if self.stop_handler is not None:
            self.stop_handler()
