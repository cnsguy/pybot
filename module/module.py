import core.module
import core.command
import core.bot_instance
import core.irc_packet

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.register_command(
            core.command.Command("mod_load", self.handle_mod_load_command, 1, "<modulnev>",
                "Betolt egy adott modult", "module.mod_load"))
        self.register_command(
            core.command.Command("mod_remove", self.handle_mod_remove_command, 1, "<modulnev>",
                "Kikapcsol egy adott modult", "module.mod_remove"))
        self.register_command(
            core.command.Command("mod_reload", self.handle_mod_reload_command, 1, "<modulnev>",
                "Ujratolt egy adott modult", "module.mod_reload"))

    def handle_mod_load_command(self, source, target, was_pm, args):
        module_name = args[0]

        if module_name in self.bot.module_instances:
            self.bot.send_message(target, "A %s modul mar be van toltve." % module_name)
            return

        try:
            self.bot.load_module(module_name)
            self.bot.send_message(target, "%s bekapcsolva." % module_name)
        except Exception as err:
            self.bot.send_message(target, "Modul betoltese sikertelen: %s" % str(err))

    def handle_mod_remove_command(self, source, target, was_pm, args):
        module_name = args[0]

        if module_name not in self.bot.module_instances:
            self.bot.send_message(target, "Nincs %s nevu modul betoltve." % module_name)
            return

        try:
            self.bot.remove_module(module_name)
            self.bot.send_message(target, "%s kikapcsolva." % module_name)
        except Exception as err:
            self.bot.send_message(target, "Modul betoltese sikertelen: %s" % err)

    def handle_mod_reload_command(self, source, target, was_pm, args):
        module_name = args[0]

        if module_name not in self.bot.module_instances:
            self.bot.send_message(target, "Nincs %s nevu modul betoltve." % module_name)
            return

        try:
            self.bot.remove_module(module_name)
            self.bot.load_module(module_name)
            self.bot.send_message(target, "%s ujratoltve." % module_name)
        except Exception as err:
            self.bot.send_message(target, "Modul ujratoltese sikertelen: %s" % err)