import core.json_data

class Module:
    def __init__(self, bot, name, stop_handler = None):
        self.bot = bot
        self.name = name
        self.packet_handlers = {}
        self.bot_event_handlers = {}
        self.commands = {}
        self.stop_handler = stop_handler

    def register_packet_handler(self, name, fn):
        assert(name not in self.packet_handlers)
        self.packet_handlers[name] = fn

    def register_command(self, command):
        self.commands[command.name] = command

    def register_bot_event(self, name, fn):
        self.bot_event_handlers[name] = fn

    def read_module_config(self, defaults):
        return core.json_data.read_json_data(defaults, "data", self.bot.db_name, "module_config", "%s.json" % self.name)

    def write_module_config(self, values):
        return core.json_data.write_json_data(values, "data", self.bot.db_name, "module_config", "%s.json" % self.name)

    def handle_packet(self, packet):
        if packet.command in self.packet_handlers:
            self.packet_handlers[packet.command](packet.source, packet.args)

    def handle_bot_event(self, name, *args):
        if name in self.bot_event_handlers:
            self.bot_event_handlers[name](*args)

    # Used in BotInstance.module_remove
    def stop(self):
        if self.stop_handler is not None:
            self.stop_handler()