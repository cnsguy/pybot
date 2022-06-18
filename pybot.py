#!/usr/bin/env python3
import core.json_data
from sys import argv, modules as sys_modules
from time import sleep

def main():
    if len(argv) < 2:
        exit("Usage: %s <config>" % argv[0])

    config_name = argv[1]

    while True:
        config = core.json_data.read_json_data({}, config_name)

        __import__("core.bot_instance")
        module = sys_modules["core.bot_instance"]
        constructor = getattr(module, "BotInstance")
        bot = constructor(
            config.get("nick", "pybot"),
            config.get("ident", "bot"),
            config.get("real_name", "ark's simple python IRC bot"),
            config["host"],
            config["port"],
            config["db_name"],
            config.get("command_prefix", "."),
            config.get("channels", []),
            config.get("debug_channel"),
            config.get("modules", [])
        )
        bot.run()

        if not bot.should_reconnect:
            break

        sleep(bot.reconnect_wait_time)
        del sys_modules["core.bot_instance"]

main()