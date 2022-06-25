import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("mod_load", self.handle_mod_load_command, 1, "<module>",
                "Loads the specified module", "module.mod_load"))
        self.register_command(
            core.command.Command("mod_remove", self.handle_mod_remove_command, 1, "<module>",
                "Removes the specified module", "module.mod_remove"))
        self.register_command(
            core.command.Command("mod_reload", self.handle_mod_reload_command, 1, "<module>",
                "Reloads the specified module", "module.mod_reload"))

    def handle_mod_load_command(self, source, target, is_pm, args):
        module_name = args[0]

        if module_name in self.bot.module_instances:
            self.bot.send_message(target, "Module '%s' is already loaded." % module_name)
            return

        try:
            self.bot.load_module(module_name)
            self.bot.send_message(target, "Module '%s' loaded." % module_name)
        except Exception as err:
            self.bot.send_message(target, "Failed to load module: %s" % str(err))

    def handle_mod_remove_command(self, source, target, is_pm, args):
        module_name = args[0]

        if module_name not in self.bot.module_instances:
            self.bot.send_message(target, "There is no module named '%s' loaded." % module_name)
            return

        try:
            self.bot.remove_module(module_name)
            self.bot.send_message(target, "Module '%s' disabled." % module_name)
        except Exception as err:
            self.bot.send_message(target, "Failed to remove module: %s" % err)

    def handle_mod_reload_command(self, source, target, is_pm, args):
        module_name = args[0]

        if module_name not in self.bot.module_instances:
            self.bot.send_message(target, "There is no module named '%s' loaded." % module_name)
            return

        try:
            self.bot.remove_module(module_name)
            self.bot.load_module(module_name)
            self.bot.send_message(target, "Module '%s' reloaded." % module_name)
        except Exception as err:
            self.bot.send_message(target, "Failed to reload module: %s" % err)