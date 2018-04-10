import datetime
import hashlib
import json
import logging
import os
import sys

from leapp.compat import string_types
from leapp.exceptions import MissingActorAttributeError, WrongAttributeTypeError
from leapp.models import Model
from leapp.tags import Tag
from leapp.utils.meta import get_flattened_subclasses


class Actor(object):
    """
    The Actor class represents the smallest step in the workflow. It defines what kind
    of data it expects, it consumes (process) a given data and produces data for other
    actors in the workflow.
    """

    name = None
    """ Name of the actor that's used to identify data/messages created by the actor. """

    description = None
    """ More verbose actor's description."""

    consumes = ()
    """
    Tuple of :py:class:`leapp.models.Model` derived classes defined in the :ref:`repositories <terminology:repository>` that
    define :ref:`messages <terminology:message>` the actor consumes.
    """

    produces = ()
    """
    Tuple of :py:class:`leapp.models.Model` derived classes defined in the :ref:`repositories <terminology:repository>` that define
    :ref:`messages <terminology:message>` the actor produces.
    """

    tags = ()
    """
    Tuple of :py:class:`leapp.tags.Tag` derived classes by which :ref:`workflow <terminology:workflow>` :ref:`phases <terminology:phase>` select
    actors for execution.
    """

    def __init__(self, messaging=None, logger=None):
        self._messaging = messaging
        self.log = (logger or logging.getLogger('leapp.actors')).getChild(self.name)
        """ A configured logger instance for the current actor """

    @property
    def actor_files_paths(self):
        """ Returns the file paths that are bundled with the actor. (Path to the content of the actor's file directory)"""
        return os.getenv("LEAPP_FILES", "").split(":")

    @property
    def files_paths(self):
        """ Returns all actor file paths (related ones to the actor and common actors files paths). """
        return self.actor_files_paths + self.common_files_paths

    @property
    def common_files_paths(self):
        """ Returns all common repository file paths. """
        return os.getenv("LEAPP_COMMON_FILES", "").split(":")

    def get_folder_path(self, name):
        """
        Finds first matching folder path within :py:attr:`files_paths`.

        :param name: Name of the folder
        :type name: str
        :return: Found folder path
        :rtype: str or None
        """
        for path in self.files_paths:
            path = os.path.join(path, name)
            if os.path.isdir(path):
                return path
        return None

    def get_file_path(self, name):
        """
        Finds first matching file path within :py:attr:`files_paths`.

        :param name: Name of the file
        :type name: str
        :return: Found file path
        :rtype: str or None
        """
        for path in self.files_paths:
            path = os.path.join(path, name)
            if os.path.isfile(path):
                return path
        return None

    def run(self, *args):
        """ Runs actor calling method :py:func:`process`. """
        os.environ['LEAPP_CURRENT_ACTOR'] = self.name
        try:
            self.process(*args)
        finally:
            os.environ.pop('LEAPP_CURRENT_ACTOR', None)

    def process(self, *args, **kwargs):
        """ Main processing method (in inherited actors, the function needs to be defined to be able process)."""
        raise NotImplementedError()

    def produce(self, *models):
        """
        By calling produce model instances are store as messages. Those messages can be then consumed by other actors.

        :param models: Messages to be sent (those model types have to be specified in :py:attr:`produces`
        :type models: Variable number of the derived classes from :py:class:`leapp.models.Model`
        """
        if self._messaging:
            for model in models:
                if isinstance(model, getattr(self.__class__, 'produces')):
                    message_data = json.dumps(model.dump(), sort_keys=True)
                    message_hash = hashlib.sha256(message_data).hexdigest()
                    self._messaging.produce(model.topic.name, {
                        'type': model.__class__.__name__,
                        'actor': self.name,
                        'topic': model.topic.name,
                        'stamp': datetime.datetime.utcnow().isoformat() + 'Z',
                        'message': {
                            'data': message_data,
                            'hash': message_hash
                        }
                    })

    def consume(self, *models):
        """
        Retrieve messages specified in the actors :py:attr:`consumes` attribute and can be filter the message types by models.

        :param models: Models to use as filter for the messages to return
        :type models: Variable number of the derived classes from :py:class:`leapp.models.Model`
        """
        if self._messaging:
            return self._messaging.consume(*models)
        return ()


def _is_type(value_type):
    def validate(actor, name, value):
        if not isinstance(value, value_type):
            raise WrongAttributeTypeError('Actor {} attribute {} should be of type {}'.format(actor, name, value_type))
        return value
    return validate


def _is_tuple_of(value_type):
    def validate(actor, name, value):
        _is_type(tuple)(actor, name, value)
        if not value:
            raise WrongAttributeTypeError(
                'Actor {} attribute {} should at least one item of type {}'.format(actor, name, value_type))
        if not all(map(lambda item: isinstance(item, value_type), value)):
            raise WrongAttributeTypeError(
                'Actor {} attribute {} should contain only value of type {}'.format(actor, name, value_type))
        return value
    return validate


def _is_model_tuple(actor, name, value):
    if isinstance(value, type) and issubclass(value, Model):
        logging.getLogger("leapp.linter").warning("Actor %s field %s should be a tuple of Models", actor, name)
        value = value,
    _is_type(tuple)(actor, name, value)
    if not all([True] + list(map(lambda item: isinstance(item, type) and issubclass(item, Model), value))):
        raise WrongAttributeTypeError(
            'Actor {} attribute {} should contain only Models'.format(actor, name))
    return value


def _is_tag_tuple(actor, name, value):
    if isinstance(value, type) and issubclass(value, Tag):
        logging.getLogger("leapp.linter").warning("Actor %s field %s should be a tuple of Tags", actor, name)
        value = value,
    _is_type(tuple)(actor, name, value)
    if not all([True] + list(map(lambda item: isinstance(item, type) and issubclass(item, Tag), value))):
        raise WrongAttributeTypeError(
            'Actor {} attribute {} should contain only Tags'.format(actor, name))
    return value


def _get_attribute(actor, name, validator, required=False, default_value=None):
    value = getattr(actor, name, None)
    if not value and required:
        raise MissingActorAttributeError('Actor {} is missing attribute {}'.format(actor, name))
    value = validator(actor, name, value)
    if not value and default_value is not None:
        value = default_value
    return name, value


def get_actor_metadata(actor):
    """
    Creates Actor's metadata dictionary

    :param actor: Actor that we want to get its metadata
    :type actor: derived class from :py:class:`leapp.actors.Actor`
    :return: Dictionary with name, tags, consumes, produces and description of the actor
    """
    return dict([
        ('class_name', actor.__name__),
        ('path', os.path.dirname(sys.modules[actor.__module__].__file__)),
        _get_attribute(actor, 'name', _is_type(string_types), required=True),
        _get_attribute(actor, 'tags', _is_tag_tuple, required=True),
        _get_attribute(actor, 'consumes', _is_model_tuple, required=False, default_value=()),
        _get_attribute(actor, 'produces', _is_model_tuple, required=False, default_value=()),
        _get_attribute(actor, 'description', _is_type(string_types), required=False,
                       default_value='There has been no description provided for this actor')
    ])


def get_actors():
    """
    :return: All actor's ancestors with their metadata
    """
    actors = get_flattened_subclasses(Actor)
    for actor in actors:
        get_actor_metadata(actor)
    return actors
