class UsageError(Exception):
    def __init__(self, message):
        super(UsageError, self).__init__(message)


class CommandDefinitionError(Exception):
    def __init__(self, message):
        super(CommandDefinitionError, self).__init__(message)


class _Empty(object):
    pass


empty = _Empty()


class Command(object):
    def __init__(self, name, target=None, help=''):
        self.name = name
        self.help = help
        self._sub_commands = {}
        self._options = []
        self.target = target
        self.parent = None
        self.parser = None

    def get_inheritable_options(self):
        return [option for option in self._options if option[2].get('inherit')]

    def called(self, args):
        if self.parent:
            self.parent.called(args)

        if self.target:
            self.target(args)

    def apply_parser(self, sparser, parent=None, parser=None):
        if self.parent is not parent:
            return

        if parser:
            self.parser = parser
        else:
            self.parser = sparser.add_parser(self.name, help=self.help)

        self.parser.set_defaults(prog=self.parser.prog, func=self.called)
        inheritable = [] if not self.parent else self.parent.get_inheritable_options()
        for args, kwargs, internal in self._options + inheritable:
            self.parser.add_argument(*args, **kwargs)

        if self._sub_commands:
            if not parser:
                subs = self.parser.add_subparsers(prog=self.parser.prog, description=self.help)
            else:
                subs = sparser
            for name, cmd in self._sub_commands.items():
                cmd.apply_parser(subs, parent=self)

    def add_sub(self, cmd):
        cmd.parent = self
        self._sub_commands[cmd.name] = cmd
        return self

    def __call__(self, name, help=''):
        def wrapper(f):
            if not hasattr(f, 'command'):
                f.command = Command(name, target=f, help=help)
            else:
                f.command.name = name
                f.command.help = help
                f.command.target = f
            self.add_sub(f.command)
            return f
        return wrapper

    def _add_opt(self, *args, **kwargs):
        internal = kwargs.pop('internal', {})
        self._options.append((args, kwargs, internal))

    def add_option(self, name, short_name='', help='', is_flag=False, inherit=False, value_type=str, wrapped=None,
                   action=None):
        name = name.lstrip('-')
        names = ['--' + name]
        kwargs = {}
        if short_name:
            short_name = short_name.lstrip('-')
            if len(short_name) != 1:
                raise CommandDefinitionError("Short name should be one letter")
            names.insert(0, '-' + short_name)
        if not action:
            action = 'store'
            if is_flag:
                action = 'store_true'
            elif value_type:
                kwargs['type'] = value_type
        self._add_opt(*names, help=help, action=action, internal={'wrapped': wrapped, 'inherit': inherit}, **kwargs)
        return self

    def add_argument(self, name, value_type=None, help='', wrapped=None):
        self._add_opt(name.replace('-', '_'), help=help, type=value_type or str, internal={'wrapped': wrapped})
        return self


def command(name, help=''):
    def wrapper(f):
        if not hasattr(f, 'command'):
            f.command = Command(name, help=help, target=f)
        else:
            f.command.name = name
            f.command.help = help
            f.command.target = f
        return f
    return wrapper


def _ensure_command(f):
    if not hasattr(f, 'command'):
        f.command = Command('')
    return f


def command_arg(name, value_type=None, help=''):
    def wrapper(f):
        _ensure_command(f).command.add_argument(name, value_type=value_type, help=help, wrapped=f)
        return f
    return wrapper


def command_opt(name, **kwargs):
    def wrapper(f):
        _ensure_command(f).command.add_option(name, wrapped=f, **kwargs)
        return f
    return wrapper
