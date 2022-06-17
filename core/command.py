import core.irc_packet
class Command:
    def __init__(self, name, handler, min_args, usage, description, acl_key = None):
        self.name = name
        self.handler = handler
        self.min_args = min_args
        self.usage = usage
        self.description = description
        self.acl_key = acl_key

    def format_help(self):
        usage = self.usage

        if usage is not None:
            return "%s %s - %s" % (self.name, usage, self.description)

        # Usage is none
        return "%s - %s" % (self.name, self.description)

    # Misc
    def execute(self, source, target, was_pm, args):
        self.handler(source, target, was_pm, args)