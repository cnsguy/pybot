import core.module
import core.command
import core.bot_instance
import core.irc_packet


class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("repeat", self.handle_repeat_command, 2, "<times> <command> (<args...>)",
                                 "Repeats a command the specified number of times with the same arguments.", "repeat.repeat"))

    def handle_repeat_command(self, source, reply_target, is_pm, args):
        try:
            times = int(args.pop(0))
        except ValueError:
            self.bot.send_message(
                reply_target, "Please specify a valid integer.")
            return

        command_name = args.pop(0)

        for _ in range(0, times):
            self.bot.run_command_by_name(
                source, command_name, reply_target, is_pm, args)
