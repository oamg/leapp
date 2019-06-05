class LeappError(Exception):
    def __init__(self, message):
        super(LeappError, self).__init__(message)
        self.message = message


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


class LeappRuntimeError(LeappError):
    pass


class StopActorExecution(Exception):
    """ This exception is used to gracefully stop execution of actor, but allows the workflow to continue. """


class StopActorExecutionError(LeappError):
    """
    This exception is used to gracefully stop execution of actor and it will call
    :py:func:`leapp.actors.Actor.report_error`.
    """
    # import here to break import cycle
    from leapp.models.error_severity import ErrorSeverity

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
