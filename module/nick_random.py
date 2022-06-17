import core.module
import core.command
import core.bot_instance
import core.irc_packet
from random import choice, randrange
from string import ascii_letters

def gen_random_nick():
    pool = ascii_letters + "_-"
    return choice(ascii_letters) + "".join([choice(pool) for _ in range(0, randrange(6, 12))])

class ModuleMain(core.module.Module):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.bot.nick = gen_random_nick()
        self.bot.ident = gen_random_nick()
        self.bot.real_name = gen_random_nick()