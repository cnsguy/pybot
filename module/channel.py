import core.channel
import core.module
import core.command
import core.bot_instance
import core.irc_packet


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)

        self.register_command(
            core.command.Command("join", self.handle_join_command, 1, "<channel>",
                                 "Joins a channel.", "channel.join"))
        self.register_command(
            core.command.Command("part", self.handle_part_command, 0, "(<channel>)",
                                 "Leaves either the specified, or the current channel.", "channel.part"))

    def handle_join_command(self, source, target, is_pm, args):
        target_channel_name = args[0]
        self.bot.send_raw_line("JOIN %s" % target_channel_name)

    def handle_part_command(self, source, target, is_pm, args):
        if len(args) > 0:
            to_part = args[0]
        else:
            if is_pm:
                return

            to_part = target

        self.bot.send_raw_line("PART %s" % to_part)
