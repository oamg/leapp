import functools
import os
import sys

from argparse import ArgumentParser, _SubParsersAction, RawDescriptionHelpFormatter

from leapp.exceptions import CommandDefinitionError, UsageError


class _LeappHelpFormatter(RawDescriptionHelpFormatter):
    """
    Capitalizes section headings in the help output
    """
    def start_section(self, heading):
        return super(_LeappHelpFormatter, self).start_section(heading.capitalize())


class _SubParserActionOverride(_SubParsersAction):
    """
    This class implements a workaround for an issue fixed in 2.7.9
    Reference: https://bugs.python.org/issue9351

    TLDR: Before 2.7.9 argparse._SubParserAction did not propagate sub parser default values
    to the global namespace when they were defined already
    This implementation is a workaround to additionally override those values

    The additional code will not be executed if python 2.7.9 or higher was found.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        super(_SubParserActionOverride, self).__call__(parser, namespace, values, option_string)
        if sys.version_info >= (2, 7, 9):
            return
        parser_name = values[0]
        arg_strings = values[1:]
        parser = self._name_parser_map[parser_name]
        sub_namespace, arg_strings = parser.parse_known_args(arg_strings, None)
        for key, value in vars(sub_namespace).items():
            setattr(namespace, key, value)


class Command(object):
    """
    Command implements a convenient command based argument parsing framework.
    """
    def __init__(self, name, target=None, help='', description=None):
        """
        :param name: Name of the sub command
        :type name: str
        :param target: Function to call when the command gets invoked
        :type target: Callable
        :param help: Help message to show
        :type help: str
        :param description: Extended description of the command (defaults to `help`)
        :type description: str
        """
        self.name = name
        self.help = help
        self.description = description or help
        self._sub_commands = {}
        self._options = []
        self.target = target
        self.parent = None
        self.parser = None

    def execute(self, version):
        """
        Entry point to command execution - Used for the main entry function of an application

        :param version: Version string to display for --version calls
        :type version: str
        :return: None
        """
        parser = ArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=_LeappHelpFormatter)
        parser.add_help
        parser.register('action', 'parsers', _SubParserActionOverride)
        parser.add_argument('--version', action='version', version=version)
        parser.set_defaults(func=None)
        s = parser.add_subparsers(title='Main commands', metavar='')
        self.apply_parser(s, parser=parser)
        args = parser.parse_args()
        args.func(args)

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
        :type args: :py:class:`argparse.Namespace`
        :return: None
        """
        try:
            if self.parent:
                self.parent.called(args)

            if self.target:
                self.target(args)
        except UsageError as e:
            self.parser.print_help(file=sys.stderr)
            self.parser.exit(status=2, message='\nUsageError: {message}\n'.format(message=e.message))

    def apply_parser(self, sparser, parent=None, parser=None):
        """
        :param sparser: ArgumentParser.add_subparsers
        :type sparser: _SubParserActionOverride
        :param parent: Instance of :py:class:`_Command`
        :type parent: _Command
        :param parser: ArgumentParser instance usually received from sparser.add_parser
        :type parser: argparse.ArgumentParser
        :return: None
        """

        if self.parent is not parent:
            return

        if parser:
            self.parser = parser
        else:
            self.parser = sparser.add_parser(self.name, help=self.help, formatter_class=_LeappHelpFormatter,
                                             description='Description:\n\n' + self.description)

        self.parser.set_defaults(prog=self.parser.prog, func=self.called)
        self.parser.register('action', 'parsers', _SubParserActionOverride)
        inheritable = []
        current = self.parent
        while current:
            inheritable += current.get_inheritable_options()
            current = current.parent
        for args, kwargs, internal in self._options + inheritable:
            self.parser.add_argument(*args, **kwargs)

        if self._sub_commands:
            if not parser:
                subs = self.parser.add_subparsers(prog=self.parser.prog, title='Available subcommands', help=self.help,
                                                  metavar='')
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

    def __call__(self, *args, **kwargs):
        kwargs['parent'] = self
        return command(*args, **kwargs)

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


def command(name, help='', description=None, parent=None):
    """
    Decorator to mark a function as sub command

    :param name: Sub command name
    :type name: str
    :param help: Help string for the sub command
    :type help: str
    :param description: Extended description for the sub command defaults to help if not set
    :type description: str
    :param parent: Instance to the parent command if it is a sub-command
    :type parent: Command
    """
    def wrapper(f):
        if not hasattr(f, 'command'):
            f.command = Command(name, help=help, target=f, description=description)
        else:
            f.command.name = name
            f.command.help = help
            f.command.description = description or help
            f.command.target = f
        if parent:
            parent.add_sub(f.command)
        return f
    return wrapper


def _ensure_command(wrapped):
    @functools.wraps(wrapped)
    def wrapper(f):
        if not hasattr(f, 'command'):
            f.command = Command('')
        return wrapped(f)
    return wrapper


def command_arg(name, value_type=None, help=''):
    """
    Decorator to wrap functions to add command line arguments to the sub command to invoke

    :param name: Name of the argument
    :param value_type: Type of the argument
    :param help: Help string for the argument
    """
    @_ensure_command
    def wrapper(f):
        f.command.add_argument(name, value_type=value_type, help=help, wrapped=f)
        return f
    return wrapper


def command_opt(name, **kwargs):
    """
    Decorator to wrap functions to add command line options to the sub command to invoke

    :param name: Name of the option
    :param kwargs: parameters as specified in :py:func:`leapp.utils.clicmd.Command.add_option`
    """
    @_ensure_command
    def wrapper(f):
        f.command.add_option(name, wrapped=f, **kwargs)
        return f
    return wrapper


def command_aware_wraps(f):
    """
    Decorator to pass through the command attribute of the wrapped function to the wrapper

    This needs to be used by decorators which are trying to wrap clicmd decorated command functions.
    """
    additional = ()
    if hasattr(f, 'command'):
        additional = ('command',)
    return functools.wraps(f, assigned=functools.WRAPPER_ASSIGNMENTS + additional)
