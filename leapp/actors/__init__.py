import logging
import os
import sys

from leapp.compat import string_types
from leapp.dialogs import Dialog
from leapp.exceptions import (MissingActorAttributeError, RequestStopAfterPhase, StopActorExecution,
                              StopActorExecutionError, WorkflowConfigNotAvailable, WrongAttributeTypeError)
from leapp.models import DialogModel, Model
from leapp.models.error_severity import ErrorSeverity
from leapp.tags import Tag
from leapp.utils import get_api_models
from leapp.utils.i18n import install_translation_for_actor
from leapp.utils.meta import get_flattened_subclasses
from leapp.workflows.api import WorkflowAPI


class Actor(object):
    """
    The Actor class represents the smallest step in the workflow. It defines what kind
    of data it expects, it consumes (processes) the given data, and it produces data for other
    actors in the workflow.
    """

    current_instance = None
    """
    Instance of the currently executed actor. Within a process only exist one Actor instance. This will allow
    convenience functions for library developers to be available.
    """

    ErrorSeverity = ErrorSeverity
    """ Convenience forward for the :py:class:`leapp.models.error_severity.ErrorSeverity` constants. """

    name = None
    """ Name of the actor that is used to identify data or messages created by the actor. """

    description = None
    """
    .. deprecated:: 0.5.0
       Write the actor's description as a docstring.
    """

    consumes = ()
    """
    Tuple of :py:class:`leapp.models.Model` derived classes defined in the :ref:`repositories <terminology:repository>`
    that define :ref:`messages <terminology:message>` the actor consumes.
    """

    produces = ()
    """
    Tuple of :py:class:`leapp.models.Model` derived classes defined in the :ref:`repositories <terminology:repository>`
    that define :ref:`messages <terminology:message>` the actor produces.
    """

    tags = ()
    """
    Tuple of :py:class:`leapp.tags.Tag` derived classes by which :ref:`workflow <terminology:workflow>`
    :ref:`phases <terminology:phase>` select actors for execution.
    """

    dialogs = ()
    """
    Tuple of :py:class:`leapp.dialogs.dialog.Dialog` derived classes that define questions to ask the user.
    Dialogs that are added to this list allow for persisting answers the user has given in the answer file storage.
    """

    apis = ()
    """
    Tuple of :py:class:`leapp.workflow.api.WorkflowAPI` derived classes that implement Workflow APIs that are used by
    an actor. Any models the apis produce or consume will be considered by the framework as if the actor defined them.
    """

    text_domain = None
    """
    Using text domain allows to override the default gettext text domain, for custom localization support.
    The default locale installation location is used which usually is /usr/share/locale
    """

    def serialize(self):
        """
        :return: Serialized information for the actor
        """
        return {
            'name': self.name,
            'path': os.path.dirname(sys.modules[type(self).__module__].__file__),
            'class_name': type(self).__name__,
            'description': self.description or type(self).__doc__,
            'consumes': [c.__name__ for c in self.consumes],
            'produces': [p.__name__ for p in self.produces],
            'tags': [t.__name__ for t in self.tags],
            'dialogs': [d.serialize() for d in self.dialogs],
        }

    def __init__(self, messaging=None, logger=None, config_model=None, skip_dialogs=False):
        self._configuration = None
        """
        Instance a workflow defined configuration model if available.

        This depends on the definition of such a configuration model being defined by the workflow
        and an actor that provides such a message.
        """
        Actor.current_instance = self
        install_translation_for_actor(type(self))
        self._messaging = messaging
        self.log = (logger or logging.getLogger('leapp.actors')).getChild(self.name)
        self.skip_dialogs = skip_dialogs
        """ A configured logger instance for the current actor. """

        if config_model:
            self._configuration = next(self.consume(config_model), None)

        # NOTE(ivasilev) Importing here because of circular dependencies
        from leapp.libraries.stdlib import path  # noqa: C415; pylint: disable=import-outside-toplevel
        self._path = path

        # Needed so produce allows to send messages for models specified also by workflow APIs
        type(self).produces = get_api_models(type(self), 'produces')

    def get_answers(self, dialog):
        """
        Gets the answers for a dialog. The dialog needs be predefined in :py:attr:`dialogs`.

        :param dialog: Dialog instance to show
        :return: dictionary with the requested answers, None if not a defined dialog
        """
        self._messaging.register_dialog(dialog, self)
        if dialog in type(self).dialogs:
            if self.skip_dialogs:
                # non-interactive mode of operation
                return self._messaging.get_answers(dialog)
            return self._messaging.request_answers(dialog)
        return None

    def show_message(self, message):
        """
        Display a message in user interterface currently in use (CLI, GUI).

        It uses one of the dialog renderers in :py:mod:`leapp.dialogs.renderer`.

        :param message: Message to show
        :type message: str
        """
        self._messaging.show_message(message)

    @property
    def configuration(self):
        """
        Returns the config model generated by specific workflow configuration actor
        """
        if not self._configuration:
            raise WorkflowConfigNotAvailable(self.name)
        return self._configuration

    @property
    def actor_files_paths(self):
        """
        Returns the file paths that are bundled with the actor. (Path to the content of the actor's file directory).
        """
        return os.getenv("LEAPP_FILES", "").split(":")

    @property
    def files_paths(self):
        """ Returns all actor file paths related to the actor and common actors file paths. """
        return self.actor_files_paths + self.common_files_paths

    @property
    def common_files_paths(self):
        """ Returns all common repository file paths. """
        return os.getenv("LEAPP_COMMON_FILES", "").split(":")

    @property
    def actor_tools_paths(self):
        """
        Returns the tool paths that are bundled with the actor. (Path to the content of the actor's tools directory).
        """
        return os.getenv("LEAPP_TOOLS", "").split(":")

    @property
    def common_tools_paths(self):
        """ Returns all common repository tool paths. """
        return os.getenv("LEAPP_COMMON_TOOLS", "").split(":")

    @property
    def tools_paths(self):
        """ Returns all actor tools paths related to the actor and common actors tools paths. """
        return self.actor_tools_paths + self.common_tools_paths


    def get_folder_path(self, name):
        """
        Finds the first matching folder path within :py:attr:`files_paths`.

        :param name: Name of the folder
        :type name: str
        :return: Found folder path
        :rtype: str or None
        """
        return self._path.get_folder_path(self.files_paths, name)

    def get_common_folder_path(self, name):
        """
        Finds the first matching folder path within :py:attr:`common_files_paths`.

        :param name: Name of the folder
        :type name: str
        :return: Found folder path
        :rtype: str or None
        """
        return self._path.get_folder_path(self.common_files_paths, name)

    def get_actor_folder_path(self, name):
        """
        Finds the first matching folder path within :py:attr:`actor_files_paths`.

        :param name: Name of the folder
        :type name: str
        :return: Found folder path
        :rtype: str or None
        """
        return self._path.get_folder_path(self.actor_files_paths, name)

    def get_file_path(self, name):
        """
        Finds the first matching file path within :py:attr:`files_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        return self._path.get_file_path(self.files_paths, name)

    def get_common_file_path(self, name):
        """
        Finds the first matching file path within :py:attr:`common_files_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        return self._path.get_file_path(self.common_files_paths, name)

    def get_actor_file_path(self, name):
        """
        Finds the first matching file path within :py:attr:`actor_files_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        return self._path.get_file_path(self.actor_files_paths, name)

    def get_tool_path(self, name):
        """
        Finds the first matching executable file path within :py:attr:`tools_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        return self._path.get_tool_path(self.tools_paths, name)

    def get_common_tool_path(self, name):
        """
        Finds the first matching executable file path within :py:attr:`common_tools_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        return self._path.get_tool_path(self.common_tools_paths, name)

    def get_actor_tool_path(self, name):
        """
        Finds the first matching executable file path within :py:attr:`actor_tools_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        return self._path.get_tool_path(self.actor_tools_paths, name)

    def run(self, *args):
        """ Runs the actor calling the method :py:func:`process`. """
        os.environ['LEAPP_CURRENT_ACTOR'] = self.name
        try:
            self.process(*args)
        except StopActorExecution:
            pass
        except StopActorExecutionError as err:
            self.report_error(err.message, err.severity, err.details)
        except RequestStopAfterPhase:
            self._messaging.request_stop_after_phase()
        finally:
            os.environ.pop('LEAPP_CURRENT_ACTOR', None)

    def process(self, *args, **kwargs):
        """ Main processing method. In inherited actors, the function needs to be defined to be able to be processed."""
        raise NotImplementedError()

    def produce(self, *models):
        """
        By calling produce, model instances are stored as messages. Those messages can be then consumed by other actors.

        :param models: Messages to be sent (those model types have to be specified in :py:attr:`produces`
        :type models: Variable number of the derived classes from :py:class:`leapp.models.Model`
        """
        if self._messaging:
            for model in models:
                if isinstance(model, type(self).produces):
                    self._messaging.produce(model, self)
                else:
                    self.log.warning('Actor is trying to produce a message of type "{}" without mentioning it '
                                     'explicitely in the actor\'s "produces" tuple. The message will be ignored'.format(
                                         type(model)))

    def consume(self, *models):
        """
        Retrieve messages specified in the actors :py:attr:`consumes` attribute, and filter message types by
        models.

        :param models: Models to use as a filter for the messages to return
        :type models: Variable number of the derived classes from :py:class:`leapp.models.Model`
        :return: All messages of the specified model(s) produced by other actors
        :rtype: Iterable with messages or an empty tuple
        """
        if self._messaging:
            return self._messaging.consume(self, *models)
        return ()

    def report_error(self, message, severity=ErrorSeverity.ERROR, details=None):
        """
        Reports an execution error

        :param message: A message to print the possible error
        :type message: str
        :param severity: Severity of the error default :py:attr:`leapp.messaging.errors.ErrorSeverity.ERROR`
        :type severity: str with defined values from :py:attr:`leapp.messaging.errors.ErrorSeverity.ERROR`
        :param details: A dictionary where additional context information is passed along with the error
        :type details: dict
        :return: None
        """
        if self._messaging:
            if not ErrorSeverity.validate(severity):
                self.log.warning("report_error: Unknown severity value %s was passed - Falling back to ERROR", severity)
                severity = ErrorSeverity.ERROR
            self._messaging.report_error(
                message=message,
                severity=severity,
                actor=self,
                details=details)


def _is_type(value_type):
    def validate(actor, name, value):
        if not isinstance(value, value_type):
            raise WrongAttributeTypeError('Actor {} attribute {} should be of the type {}'.format(actor, name,
                                                                                                  value_type))
        return value
    return validate


def _is_tuple_of(value_type):
    def validate(actor, name, value):
        _is_type(tuple)(actor, name, value)
        if not value:
            raise WrongAttributeTypeError(
                'Actor {} attribute {} should contain at least one item of the type {}'.format(actor, name, value_type))
        if not all([isinstance(item, value_type) for item in value]):
            raise WrongAttributeTypeError(
                'Actor {} attribute {} should contain only values of the type {}'.format(actor, name, value_type))
        return value
    return validate


def _lint_warn(actor, name, type_name):
    warnings = getattr(actor, '_warnings', {})
    if not warnings.get(name + '_tuple'):
        warnings[name + '_tuple'] = True
        setattr(actor, '_warnings', warnings)
        logging.getLogger("leapp.linter").warning("Actor %s field %s should be a tuple of %s", actor, name, type_name)


def _is_model_tuple(actor, name, value):
    if isinstance(value, type) and issubclass(value, Model):
        _lint_warn(actor, name, "Models")
        value = (value,)
    _is_type(tuple)(actor, name, value)
    if not all([True] + [isinstance(item, type) and issubclass(item, Model) for item in value]):
        raise WrongAttributeTypeError(
            'Actor {} attribute {} should contain only Models'.format(actor, name))
    return value


def _is_dialog_tuple(actor, name, value):
    if isinstance(value, Dialog):
        _lint_warn(actor, name, "Dialogs")
        value = (value,)
    _is_type(tuple)(actor, name, value)
    if not all([True] + [isinstance(item, Dialog) for item in value]):
        raise WrongAttributeTypeError(
            'Actor {} attribute {} should contain only Dialogs'.format(actor, name))
    return value


def _is_tag_tuple(actor, name, value):
    if isinstance(value, type) and issubclass(value, Tag):
        _lint_warn(actor, name, "Tags")
        value = (value,)
    _is_type(tuple)(actor, name, value)
    if not all([True] + [isinstance(item, type) and issubclass(item, Tag) for item in value]):
        raise WrongAttributeTypeError(
            'Actor {} attribute {} should contain only Tags'.format(actor, name))
    return value


def _is_api_tuple(actor, name, value):
    if isinstance(value, type) and issubclass(value, WorkflowAPI):
        _lint_warn(actor, name, "Apis")
        value = (value,)
    _is_type(tuple)(actor, name, value)
    if not all([True] + [isinstance(item, type) and issubclass(item, WorkflowAPI) for item in value]):
        raise WrongAttributeTypeError(
            'Actor {} attribute {} should contain only WorkflowAPIs'.format(actor, name))
    return value


def _get_attribute(actor, name, validator, required=False, default_value=None, additional_info='', resolve=None):
    if resolve:
        value = resolve(actor, name)
    else:
        value = getattr(actor, name, None)
    if not value and required:
        raise MissingActorAttributeError('Actor {} is missing attribute {}.{}'.format(actor, name, additional_info))
    if value or required:
        value = validator(actor, name, value)
    if not value and default_value is not None:
        value = default_value
    return name, value


def get_actor_metadata(actor):
    """
    Creates Actor's metadata dictionary

    :param actor: Actor whose metadata are needed
    :type actor: derived class from :py:class:`leapp.actors.Actor`
    :return: Dictionary with the name, tags, consumes, produces, and description of the actor
    """
    additional_tag_info = ' At least one tag is required for actors. Please fill the tags field'
    return dict([
        ('class_name', actor.__name__),
        # TODO: missing tests. We need to ensure this doesn't break anything.
        # # OTOH, actor_definition.inspect_actor ends with empty list on Python3
        # # if path is not transformed into the realpath.
        ('path', os.path.dirname(os.path.realpath(sys.modules[actor.__module__].__file__))),
        _get_attribute(actor, 'name', _is_type(string_types), required=True),
        _get_attribute(actor, 'tags', _is_tag_tuple, required=True, additional_info=additional_tag_info),
        _get_attribute(actor, 'consumes', _is_model_tuple, required=False, default_value=(), resolve=get_api_models),
        _get_attribute(actor, 'produces', _is_model_tuple, required=False, default_value=(), resolve=get_api_models),
        _get_attribute(actor, 'dialogs', _is_dialog_tuple, required=False, default_value=()),
        _get_attribute(actor, 'description', _is_type(string_types), required=False,
                       default_value=actor.__doc__ or 'There has been no description provided for this actor.'),
        _get_attribute(actor, 'apis', _is_api_tuple, required=False, default_value=())
    ])


def get_actors():
    """
    :return: All registered actors with their metadata
    """
    actors = get_flattened_subclasses(Actor)
    for actor in actors:
        get_actor_metadata(actor)
    return actors
