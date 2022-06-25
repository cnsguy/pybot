import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("help", self.handle_help_command, 0, "(<command>)", 
                "Displays help for the specified command, or if no command is specified, lists all available ones."))

    def handle_help_command(self, source, target, is_pm, args):
        if len(args) > 0:
            # Help about a specific command
            command_name = args[0]
            command = None

            for module in self.bot.module_instances.values():
                if command_name in module.commands:
                    command = module.commands[command_name]
                    break

            if command is None:
                self.bot.send_message(target, "No such command exists.")
            else:
                command_help = command.format_help()
                self.bot.send_message(target, self.bot.command_prefix + command_help)
        else:
            # List commands in general
            result = []

            for module in self.bot.module_instances.values():
                sub_result = []
                sub_result.append("[%s]" % module.name)

                for command in module.commands.values():
                    sub_result.append(self.bot.command_prefix + command.name)

                result.append(" ".join(sub_result))

            self.bot.send_message(target, " ".join(result))