import core.channel
import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.config = self.read_module_config({
            "channels": [] # List of channel names to join
        })

        self.register_packet_handler("001", self.handle_connected)
        self.register_command(
            core.command.Command("join", self.handle_join_command, 1, "<channel>", 
                "Csatlakozik az adott csatornahoz.", "channel.join"))
        self.register_command(
            core.command.Command("part", self.handle_part_command, 0, "(<channel>)",
                "Elhagyja az adott, vagy a jelenlegi csatornat.", "channel.part"))

    def handle_connected(self, source, args):
        for channel_name in self.config["channels"]:
            self.bot.send_raw_line("JOIN %s" % channel_name)

    def handle_join_command(self, source, target, was_pm, args):
        target_channel_name = args[0]
        self.bot.send_raw_line("JOIN %s" % target_channel_name)

        if target_channel_name not in self.config["channels"]:
            self.config["channels"].append(target_channel_name)
            self.write_module_config(self.config)

    def handle_part_command(self, source, target, was_pm, args):
        if len(args) > 0:
            to_part = args[0]
        else:
            if was_pm:
                return

            to_part = target

        self.bot.send_raw_line("PART %s" % to_part)