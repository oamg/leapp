import functools
import os
import sys
from argparse import (ArgumentParser, RawDescriptionHelpFormatter,
                      _SubParsersAction)

import six
from leapp.exceptions import (CommandDefinitionError, CommandError,
                              UnknownCommandError, UsageError)


class _LeappArgumentParser(ArgumentParser):
    def print_help(self):
        super(_LeappArgumentParser, self).print_help(file=sys.stderr)

    def error(self, message):
        self.print_help()
        sys.stderr.write('error: %s\n' % message)
        sys.exit(2)


class _LeappHelpFormatter(RawDescriptionHelpFormatter):
    """
    Capitalizes section headings in the help output
    """

    def start_section(self, heading):
        return super(_LeappHelpFormatter, self).start_section(heading.capitalize())


class _SubParserActionOverride(_SubParsersAction):
    """
    This class implements a workaround for an issue fixed in 2.7.9.
    See https://bugs.python.org/issue9351

    TL;DR: Before, 2.7.9 argparse._SubParserAction did not propagate sub parser default values
    to the global namespace when they were already defined .
    This implementation is a workaround to override those values additionally.

    The additional code will not be executed if python 2.7.9 or higher is found.
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
    Command implements a convenient command-based argument parsing the framework.
    """

    def __init__(self, name, target=None, help='', description=None):  # noqa; pylint: disable=redefined-builtin
        """
        :param name: Name of the sub command
        :type name: str
        :param target: Function called when the command is invoked
        :type target: Callable
        :param help: Shows a help message
        :type help: str
        :param description: Extended description of the command (the default is `help`)
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
        Entry point to the command execution. It is used for the main entry function of an application.

        :param version: Version string to display for --version calls
        :type version: str
        :return: None
        """
        parser = _LeappArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=_LeappHelpFormatter)
        parser.register('action', 'parsers', _SubParserActionOverride)
        parser.add_argument('--version', action='version', version=version)
        parser.set_defaults(func=None)
        if self._sub_commands:
            s = parser.add_subparsers(title='Required arguments', metavar='command')
            s.required = True
        else:
            s = parser
        self.apply_parser(s, parser=parser)
        # NOTE(ivasilev) a clumsy hack to make leapp output help information for the
        # exact subcommand that has been called.
        # The original problem was with parser.parse_args() referring to parser for
        # topmost leapp command and not the subcommand during error processing.
        # Any ideas and proposals on a more elegant solution are welcome.
        args, leftover = parser.parse_known_args()
        if leftover:
            cmdname = args.prog.split()[-1]
            if cmdname not in self._sub_commands:
                cmdname = leftover[0]
            if cmdname not in self._sub_commands:
                raise UnknownCommandError(cmdname)
            self._sub_commands[cmdname].parser.error(leftover)
        args.func(args)

    def get_inheritable_options(self):
        """
        :return: Returns all options that are marked as 'inherit'
        """
        return [option for option in self._options if option[2].get('inherit')]

    def called(self, args):
        """
        The actual call is dispatched through this method. It ensures that the parent is also called
        to allow generic handling of some flags (especially inherited flags).

        :param args: Arguments object that is a result of the `argparse` commandline parser
        :type args: :py:class:`argparse.Namespace`
        :return: None
        """
        try:
            if self.parent:
                self.parent.called(args)

            if self.target:
                self.target(args)
        except UsageError as e:
            self.parser.print_help()
            self.parser.exit(status=2, message='\nUsageError: {message}\n'.format(message=e.message))
        except CommandError as e:
            self.parser.exit(status=2, message='\nError: {message}\n'.format(message=e.message))

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
                subs = self.parser.add_subparsers(prog=self.parser.prog, title='Available subcommands',
                                                  help=self.help,  # noqa; pylint: disable=redefined-builtin
                                                  metavar='')
            else:
                subs = sparser
            for name, cmd in self._sub_commands.items():
                cmd.apply_parser(subs, parent=self)

    def add_sub(self, cmd):
        """
        Adds a sub command to this command

        :param cmd: The sub command object
        :type cmd: :py:class:`leapp.utils.clicmd.Command`
        :return: self
        """
        if not isinstance(cmd, Command):
            if isinstance(getattr(cmd, 'command', None), Command):
                cmd = cmd.command
            else:
                raise TypeError('Expected instance of Command or decorated command function as parameter')
        cmd.parent = self
        self._sub_commands[cmd.name] = cmd
        return self

    def __call__(self, *args, **kwargs):
        kwargs['parent'] = self
        return command(*args, **kwargs)

    def _add_opt(self, *args, **kwargs):
        internal = kwargs.pop('internal', {})
        self._options.append((args, kwargs, internal))

    def add_option(self, name, short_name='', help='',  # noqa; pylint: disable=redefined-builtin
                   is_flag=False, inherit=False, value_type=str, wrapped=None, action=None, metavar=None,
                   choices=None, default=None):
        """
        Add an option

        :param name: Name of the option
        :type name: str
        :param short_name: Short name of the option (one letter)
        :type short_name: str
        :param help: Help string for the option
        :type help: str
        :param is_flag: Decides if it is a flag
        :type is_flag: bool
        :param inherit: Decides if this option should be inherited by sub commands
        :type inherit: bool
        :param value_type: Type of the value by default string
        :param wrapped: Function that is wrapped (aka the target)
        :type wrapped: Callable
        :param action: ArgumentParser actions to take (e.g. store)
        :type action: str
        :param metavar: Changes the display name of arguments in generated help messages.
                        It has no influence on the attribute name from the generated arguments namespace.
        :type metavar: str
        :param choices: range of values that the argument is allowed to take
        :type choices: list
        :param default: default value of the argument if nothing is specified
        :type default: any
        :return: self
        """
        name = name.lstrip('-')
        names = ['--' + name]
        kwargs = {}
        if short_name:
            short_name = short_name.lstrip('-')
            if len(short_name) != 1:
                raise CommandDefinitionError("Short name should be one letter only")
            names.insert(0, '-' + short_name)
        if not action:
            action = 'store'
            if is_flag:
                action = 'store_true'
            elif value_type:
                kwargs['type'] = value_type
        if metavar:
            kwargs['metavar'] = metavar
        if choices:
            kwargs['choices'] = choices
        if default is not None:
            kwargs['default'] = default
        self._add_opt(*names, help=help,  # noqa; pylint: disable=redefined-builtin
                      action=action, internal={'wrapped': wrapped, 'inherit': inherit}, **kwargs)
        return self

    def add_argument(self, name, value_type=None, help='', wrapped=None):  # noqa; pylint: disable=redefined-builtin
        """

        :param name:
        :param value_type:
        :param help:
        :param wrapped:
        :return:
        """
        self._add_opt(name.replace('-', '_'), help=help,  # noqa; pylint: disable=redefined-builtin
                      type=value_type or str, internal={'wrapped': wrapped})
        return self


def command(name, help='', description=None, parent=None):  # noqa; pylint: disable=redefined-builtin
    """
    Decorator to mark a function as a sub command

    :param name: Sub command name
    :type name: str
    :param help: Help string for the sub command
    :type help: str
    :param description: Extended description for the sub command defaults to help if it is not set
    :type description: str
    :param parent: Instance to the parent command if it is a sub-command
    :type parent: Command
    """
    def wrapper(f):
        if not hasattr(f, 'command'):
            f.command = Command(name, help=help,  # noqa; pylint: disable=redefined-builtin
                                target=f, description=description)
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
    @six.wraps(wrapped)
    def wrapper(f):
        if not hasattr(f, 'command'):
            f.command = Command('')
        return wrapped(f)
    return wrapper


def command_arg(name, value_type=None, help=''):  # noqa; pylint: disable=redefined-builtin
    """
    Decorator wrapping functions to add command line arguments to the sub command to be invoked

    :param name: Name of the argument
    :param value_type: Type of the argument
    :param help: Help string for the argument
    """
    @_ensure_command
    def wrapper(f):
        f.command.add_argument(name, value_type=value_type, help=help,  # noqa; pylint: disable=redefined-builtin
                               wrapped=f)
        return f
    return wrapper


def command_opt(name, **kwargs):
    """
    Decorator wrapping functions to add command line options to the sub command to be invoked

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
    Decorator passing the command attribute of the wrapped function to the wrapper

    This needs to be used by decorators that are trying to wrap clicmd decorated command functions.
    """
    additional = ()
    if hasattr(f, 'command'):
        additional = ('command',)
    return six.wraps(f, assigned=functools.WRAPPER_ASSIGNMENTS + additional)
