class LeappError(Exception):
    def __init__(self, message):
        super(LeappError, self).__init__(message)
        self.message = message


class FrameworkInitializationError(LeappError):
    pass


class RepositoryConfigurationError(LeappError):
    pass


class CannotConsumeErrorMessages(LeappError):
    def __init__(self):
        super(CannotConsumeErrorMessages, self).__init__("Actors cannot consume error messages.")


class InvalidTopicItemError(LeappError):
    pass


class InvalidTopicDefinitionError(LeappError):
    pass


class InvalidTagDefinitionError(LeappError):
    pass


class MissingActorAttributeError(LeappError):
    pass


class WrongAttributeTypeError(LeappError):
    pass


class ModelDefinitionError(LeappError):
    pass


class TagFilterUsageError(LeappError):
    pass


class CyclingDependenciesError(LeappError):
    pass


class UnsupportedDefinitionKindError(LeappError):
    pass


class ModuleNameAlreadyExistsError(LeappError):
    pass


class ActorInspectionFailedError(LeappError):
    pass


class MultipleActorsError(LeappError):
    def __init__(self, path):
        super(MultipleActorsError, self).__init__(
            'Multiple actors found in {path}. Inspection failed'.format(path=path))


class MultipleConfigActorsError(LeappError):
    def __init__(self, config_actors):
        super(MultipleConfigActorsError, self).__init__(
            'Multiple config actors detected: {config_actors}. '
            'Only one config actor per workflow is allowed'.format(config_actors=config_actors))


class WorkflowConfigNotAvailable(LeappError):
    def __init__(self, actor):
        # TODO(mreznik): Current implementation of the workflow congiguration is problematic when used
        # with snactor. See https://github.com/oamg/leapp/issues/530
        super(WorkflowConfigNotAvailable, self).__init__(
            'Actor {actor} relies on workflow configuration model which '
            'must be produced by a specific actor'.format(actor=actor))


class RepoItemPathDoesNotExistError(LeappError):
    def __init__(self, kind, rel_path, full_path):
        super(RepoItemPathDoesNotExistError, self).__init__(
            'Could not find {kind} item with relative path: {rel_path} at {full_path}'.format(
                kind=kind, rel_path=rel_path, full_path=full_path))


class ActorDiscoveryExecutionError(LeappError):
    pass


class UsageError(LeappError):
    pass


class CommandError(LeappError):
    pass


class CommandDefinitionError(LeappError):
    pass


class UnknownCommandError(LeappError):
    def __init__(self, command):
        super(UnknownCommandError, self).__init__('Unknown command: {}'.format(command))
        self.requested = command


class LeappRuntimeError(LeappError):
    def __init__(self, message, exception_info=None):
        super(LeappRuntimeError, self).__init__(message)
        self.exception_info = exception_info


class StopActorExecution(Exception):
    """ This exception is used to gracefully stop execution of actor, but allows the workflow to continue. """


class StopActorExecutionError(LeappError):
    """
    This exception is used to gracefully stop execution of actor and it will call
    :py:func:`leapp.actors.Actor.report_error`.
    """
    # import here to break import cycle
    from leapp.models.error_severity import ErrorSeverity  # pylint: disable=import-outside-toplevel

    def __init__(self, message, severity=ErrorSeverity.ERROR, details=None):
        """
        :param message: A message to print the possible error
        :type message: str
        :param severity: Severity of the error default :py:attr:`leapp.messaging.errors.ErrorSeverity.ERROR`
        :type severity: str with defined values from :py:attr:`leapp.messaging.errors.ErrorSeverity.ERROR`
        :param details: A dictionary where additional context information is passed along with the error
        :type details: dict
        """
        super(StopActorExecutionError, self).__init__(message)
        self.severity = severity
        self.details = details


class RequestStopAfterPhase(LeappError):
    """
    This exception is used to gracefully stop the current actor and request the stop of the workflow execution after
    the current phase.
    """

    def __init__(self):
        super(RequestStopAfterPhase, self).__init__('Stop after phase has been requested.')


class ProcessLockError(LeappError):
    """ This exception is used to represent an error within the process locking mechanism. """
