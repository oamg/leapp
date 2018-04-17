from leapp.exceptions import CommandDefinitionError


class Command(object):
    """
    Command implements a convenient command based argument parsing framework.
    """
    def __init__(self, name, target=None, help=''):
        """
        :param name: Name of the sub command
        :param target: Function to call when the command gets invoked
        :param help: Help message to show
        """
        self.name = name
        self.help = help
        self._sub_commands = {}
        self._options = []
        self.target = target
        self.parent = None
        self.parser = None

    def get_inheritable_options(self):
        """
        :return: Returns all options that are marked as 'inherit'
        """
        return [option for option in self._options if option[2].get('inherit')]

    def called(self, args):
        """
        The actual call is dispatched through this method - It will ensure that the parent is called as well
        for allowing some generic handling of some flags (especially inherited flags)

        :param args: Arguments object that is the result of the `argparse` commandline parser
        :return: None
        """
        if self.parent:
            self.parent.called(args)

        if self.target:
            self.target(args)

    def apply_parser(self, sparser, parent=None, parser=None):
        """
        :param sparser: ArgumentParser.add_subparsers
        :param parent: Instance of :py:ref:`_Command`
        :param parser: ArgumentParser instance usually received from sparser.add_parser
        :return: None
        """

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
        """
        Add a sub command to this command

        :param cmd: The sub command object
        :type cmd: :py:class:`leapp.utils.clicmd.Command`
        :return: self
        """
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
        """
        Add an option

        :param name: Name of the option
        :type name: str
        :param short_name: short name of the option (One letter)
        :type short_name: str
        :param help: Help string for the option
        :type help: str
        :param is_flag: If it is a flag
        :type is_flag: bool
        :param inherit: Should this option be inherited by sub commands?
        :type inherit: bool
        :param value_type: Type of the value by default string
        :param wrapped: Function that is wrapped (aka the target)
        :type wrapped: Callable
        :param action: ArgumentParser actions to take (e.g. store)
        :type action: str
        :return: self
        """
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
        """

        :param name:
        :param value_type:
        :param help:
        :param wrapped:
        :return:
        """
        self._add_opt(name.replace('-', '_'), help=help, type=value_type or str, internal={'wrapped': wrapped})
        return self


def command(name, help=''):
    """
    Decorator to mark a function as sub command

    :param name: Sub command name
    :param help: Help string for the sub command
    """
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
    """
    Decorator to wrap functions to add command line arguments to the sub command to invoke

    :param name: Name of the argument
    :param value_type: Type of the argument
    :param help: Help string for the argument
    """
    def wrapper(f):
        _ensure_command(f).command.add_argument(name, value_type=value_type, help=help, wrapped=f)
        return f
    return wrapper


def command_opt(name, **kwargs):
    """
    Decorator to wrap functions to add command line options to the sub command to invoke

    :param name: Name of the option
    :param kwargs: parameters as specified in :py:func:`leapp.utils.clicmd.Command.add_option`
    """
    def wrapper(f):
        _ensure_command(f).command.add_option(name, wrapped=f, **kwargs)
        return f
    return wrapper
