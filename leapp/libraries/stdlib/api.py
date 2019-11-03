"""
This module implements a convenience API for actions that are accessible to actors.

Any code that wants use this convenience library has to be called from within the actors context.
This is true for actors, actor private libraries and repository libraries.
"""
import logging

from leapp.actors import Actor


ErrorSeverity = Actor.ErrorSeverity


def current_actor():
    """
    Retrieve the Actor class instance of the current active actor.
    :return: Instance of the currently instantiated actor.
    :rtype: leapp.actors.Actor
    """
    return Actor.current_instance


def report_error(message, severity=ErrorSeverity.ERROR, details=None):
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
    return current_actor().report_error(message=message, severity=severity, details=details)


def show_message(message):
    """
    Display a message in user interterface currently in use (CLI, GUI).

    It uses one of the dialog renderers in :py:mod:`leapp.dialogs.renderer`.

    :param message: Message to show
    :type message: str
    """
    return current_actor().show_message(message=message)


def current_logger():
    """
    Retrieve the logger of the current active actor.
    :return: Logger instance for the current actor.
    :rtype: logging.Logger
    """
    return current_actor().log if current_actor() else logging.getLogger('leapp.fallback')


def produce(*model_instances):
    """
    By calling produce, model instances are stored as messages. Those messages can be then consumed by other actors.

    :param model_instances: Messages to be sent (those model types have to be specified in :py:attr:`produces`
    :type model_instances: Variable number of instances of derived classes from :py:class:`leapp.models.Model`
    """
    return current_actor().produce(*model_instances)


def consume_first_default(model):
    """
    Retrieves the first message found as specified in the actors :py:attr:`consumes` attribute, and filter message
    types by model. This additionally returns as fallback value an instance of model with the default
    initialization

    :param model: Model to use as a filter for the messages to return
    :type model: A derived class from :py:class:`leapp.models.Model`
    :return: The first message of the specified model produced by other a fallback instance of model
    :rtype: The message or a default initialized instance of the model type.
    """
    return current_actor().consume_first_default(model)


def consume_first(model, default=None):
    """
    Retrieves the first message found as specified in the actors :py:attr:`consumes` attribute, and filter message
    types by model.

    :param model: Model to use as a filter for the messages to return
    :type model: A derived class from :py:class:`leapp.models.Model`
    :param default: Fallback value in case there are no messages
    :type default: Any
    :return: The first message of the specified model produced by other actors or the value passed as `default`
    :rtype: The message or the value passed as ``default``
    """
    return current_actor().consume_first(model=model, default=default)


def consume(*models):
    """
    Retrieve messages specified in the actors :py:attr:`consumes` attribute, and filter message types by
    models.

    :param models: Models to use as a filter for the messages to return
    :type models: Variable number of the derived classes from :py:class:`leapp.models.Model`
    """
    return current_actor().consume(*models)


def request_answers(dialog):
    """
    Requests the answers for a dialog. The dialog needs be predefined in :py:attr:`dialogs` of the actor.

    :param dialog: Dialog instance to show
    :return: dictionary with the requested answers, None if not a defined dialog
    """
    return current_actor().request_answers(dialog)


def actor_files_paths():
    """
    Returns the file paths that are bundled with the actor. (Path to the content of the actor's file directory).
    """
    return current_actor().actor_files_paths


def files_paths():
    """ Returns all actor file paths related to the actor and common actors file paths. """
    return current_actor().files_paths


def common_files_paths():
    """ Returns all common repository file paths. """
    return current_actor().common_files_paths


def actor_tools_paths():
    """
    Returns the tool paths that are bundled with the actor. (Path to the content of the actor's tools directory).
    """
    return current_actor().actor_tools_paths


def tools_paths():
    """ Returns all actor tools paths related to the actor and common actors tools paths. """
    return current_actor().tools_paths


def common_tools_paths():
    """ Returns all common repository tool paths. """
    return current_actor().common_tools_paths


def get_common_folder_path(name):
    """
    Finds the first matching folder path within :py:attr:`files_paths`.

    :param name: Name of the folder
    :type name: str
    :return: Found folder path
    :rtype: str or None
    """
    return current_actor().get_common_folder_path(name)


def get_actor_folder_path(name):
    """
    Finds the first matching folder path within :py:attr:`files_paths`.

    :param name: Name of the folder
    :type name: str
    :return: Found folder path
    :rtype: str or None
    """
    return current_actor().get_actor_folder_path(name)


def get_folder_path(name):
    """
    Finds the first matching folder path within :py:attr:`files_paths`.

    :param name: Name of the folder
    :type name: str
    :return: Found folder path
    :rtype: str or None
    """
    return current_actor().get_folder_path(name)


def get_common_file_path(name):
    """
    Finds the first matching file path within :py:attr:`files_paths`.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    return current_actor().get_common_file_path(name)


def get_actor_file_path(name):
    """
    Finds the first matching file path within :py:attr:`files_paths`.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    return current_actor().get_actor_file_path(name)


def get_file_path(name):
    """
    Finds the first matching file path within :py:attr:`files_paths`.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    return current_actor().get_file_path(name)


def get_tool_path(name):
    """
    Finds the first matching executable file path within :py:attr:`tools_paths`.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    return current_actor().get_tool_path(name)


def get_common_tool_path(name):
    """
    Finds the first matching executable file path within :py:attr:`common_tools_paths`.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    return current_actor().get_common_tool_path(name)


def get_actor_tool_path(name):
    """
    Finds the first matching executable file path within :py:attr:`actor_tools_paths`.

    :param name: Name of the file
    :type name: str
    :return: Found file path
    :rtype: str or None
    """
    return current_actor().get_actor_tool_path(name)
