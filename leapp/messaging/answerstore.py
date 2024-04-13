import multiprocessing

import six
from six.moves import configparser
try:
    from six.moves.configparser import SafeConfigParser as ConfigParser
except ImportError:
    from six.moves.configparser import ConfigParser

from leapp.exceptions import CommandError
from leapp.utils.audit import create_audit_entry


def _comment_out(key, text):
    """Returns a commented-out string. If any newlines are present it properly deals with them"""
    text = str(text)
    split_by_newline = [s for s in text.split('\n') if s.strip()]
    res = '# {key:<20}{line1}\n{linesN}'.format(key='{}:'.format(key) if key else '',
                                                line1=split_by_newline[0],
                                                linesN=''.join([_comment_out('', line)
                                                                for line in split_by_newline[1:]]))
    return res


class AnswerStore(object):
    """
    AnswerStore handles storing and loading answer files for user questions.
    """

    def __init__(self, manager=None):
        """
        Initialize the answer store.
        :param manager: Passes through a given instance of multiprocessing.Manager() to use, by default it creates
                        an own instance.
        """
        self._manager = manager or multiprocessing.Manager()
        self._storage = self._manager.dict()

    def answer(self, scope, key, value):
        dialog_scope = self._storage.get(scope, {})
        dialog_scope[key] = value
        # As _storage is a dict proxy, we have to explicitly update the object via __setitem__
        # Otherwise we won't get the update propagated to the parent process
        # So don't even bother updating this to some more 'pythonic' coding style
        self._storage[scope] = dialog_scope

    @classmethod
    def _load_ini(cls, inifile):
        """
        Loads an ini config file from the given location.

        :param inifile: Path to the answer file to load.
        :return: configparser.ConfigParser object
        :raises CommandError if any of the values are not in key=value format
        """
        conf = ConfigParser(allow_no_value=False)

        try:
            conf.read(inifile)
            return conf
        except configparser.ParsingError as exc:
            # Some of the sections were not in key = value format
            raise CommandError('Failed to load answer file {inifile} with the following errors: {errors}'.format(
                inifile=inifile, errors=exc.message))

    def update(self, answer_file, allow_missing=False):
        """
        Update answerfile with all answers from answerstore that have correspondent sections in the file.

        Returns a list of sections that were not found in original answerfile and thus were not updated.
        """
        # NOTE(ivasilev): py2 configparser doesn't have any means to save comments in ini file. Switch to cfgparse?
        conf = AnswerStore._load_ini(answer_file)
        not_updated = []
        for section, answerdict in self._storage.items():
            for opt, val in answerdict.items():
                if section not in conf.sections() and allow_missing:
                    conf.add_section(section)
                try:
                    conf.set(section, opt, str(val))
                except configparser.NoSectionError:
                    not_updated.append("{sec}.{opt}={val}".format(sec=section, opt=opt, val=val))
        with open(answer_file, 'w') as afile:
            conf.write(afile)
        return not_updated

    def load(self, answer_file):
        """
        Loads an answer file from the given location and updates the loaded data with it.

        :param answer_file: Path to the answer file to load.
        :return: None
        :raises CommandError if any of the values are not in key=value format
        """
        conf = AnswerStore._load_ini(answer_file)
        for section in conf.sections():
            self._storage[section] = self._manager.dict(conf.items(section=section, raw=True))

    def load_and_translate_for_workflow(self, answer_file, workflow):
        """
        Loads an answer file from the given location and updates the loaded data with it and translates the data to
        the correct value types based on the dialogs in the given workflow.

        :param answer_file: Path to the answer file to load.
        :param workflow:
        :return: None
        :raises CommandError if any of the values are not in key=value format
        """
        conf = AnswerStore._load_ini(answer_file)
        for section in conf.sections():
            self._storage[section] = dict(conf.items(section=section, raw=True))
        self.translate_for_workflow(workflow)

    def get(self, scope, fallback=None):
        """
        Dict compatible interface to get a sub dictionary by dialog scope.

        :param scope: Scope of the data to retrieve.
        :param fallback: Fallback value to return if not found.
        :return: A shallow copy of data stored in _storage by scope key
        """
        # NOTE(ivasilev) self.storage.get() will return a DictProxy. To avoid TypeError during later
        # JSON serialization a copy() should be invoked to get a shallow copy of data
        answer = self._storage.get(scope, fallback).copy()

        # NOTE(dkubek): It is possible that we do not need to save the 'answer'
        # here as it is being stored with dialog question right after query
        create_audit_entry('dialog-answer', {'scope': scope, 'fallback': fallback, 'answer': answer})
        return answer

    def translate_for_workflow(self, workflow):
        """
        Translates the data for all dialogs in the current workflow.

        :param workflow: Instance of a workflow to translate all dialogs from.
        :type workflow: :py:class:`leapp.workflows.Workflow`
        :return: None
        """
        for dialog in workflow.dialogs:
            self.translate(dialog)

    def translate(self, dialog):
        """
        Translates configuration values from their string form to the corresponding value format based on the given
        dialog.

        :param dialog: A dialog instance to translate the data for.
        :type dialog: :py:class:`leapp.dialogs.dialog.Dialog`
        :return: None
        """
        entry = self._storage.get(dialog.scope)
        if entry:
            for component in dialog.components:
                if component.key in entry and isinstance(entry[component.key], six.string_types):
                    if component.value_type is bool:
                        entry[component.key] = entry[component.key].lower() == 'true'
                    elif component.value_type is int:
                        entry[component.key] = int(entry[component.key])
                    elif component.value_type is tuple:
                        elements = entry[component.key].split(';')
                        entry[component.key] = tuple(set(elements).intersection(component.choices))
                    elif hasattr(component, 'choices'):
                        value = entry[component.key]
                        entry[component.key] = value if value in component.choices else None
                    component.value = entry.get(component.key)
            self._storage.update({dialog.scope: entry})

    def generate(self, dialogs, answer_file_path):
        """
        Generates an answer file for the given dialogs and stores it to `answer_file_path`.
        :param dialogs:
        :param answer_file_path:
        :return:
        """

        with open(answer_file_path, 'w') as f:
            for dialog in dialogs:
                if not dialog.components:
                    # Skip dialogs without questions
                    continue

                f.writelines([
                    '[{}]\n'.format(dialog.scope),
                    _comment_out('Title', dialog.title),
                    _comment_out('Reason', dialog.reason)
                ])

                for component in dialog.components:
                    answer = self._storage.get(dialog.scope, {}).get(component.key)
                    default = component.default
                    choices = ''
                    answer_entry = ''
                    if hasattr(component, 'choices'):
                        choices += '# Available choices: {}\n'.format('/'.join(component.choices))
                        if component.value_type is tuple:
                            default = ';'.join(component.default)
                            answer = ';'.join(answer) if answer else answer
                            answer_entry = '#\n# Values are separated by semi-colon ";"\n'
                    if answer is not None:
                        answer_entry += '{key} = {value}\n'.format(key=component.key, value=answer)
                    else:
                        answer_entry += '# Unanswered question. Uncomment the following line with your answer\n'
                        answer_entry += '# {key} = {value}\n'.format(key=component.key, value=default or '')

                    f.writelines([
                        '# {}\n'.format(' {}.{} '.format(dialog.scope, component.key).center(77, '=')),
                        _comment_out('Label', component.label),
                        _comment_out('Description', component.description),
                        _comment_out('Reason', component.reason),
                        _comment_out('Type', component.value_type.__name__),
                        _comment_out('Default', default),
                        choices,
                        answer_entry,
                        '\n'
                    ])
