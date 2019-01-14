class LeappError(Exception):
    def __init__(self, message):
        super(LeappError, self).__init__(message)
        self.message = message


class RepositoryConfigurationError(LeappError):
    def __init__(self, message):
        super(RepositoryConfigurationError, self).__init__(message)


class CannotConsumeErrorMessages(LeappError):
    def __init__(self):
        super(CannotConsumeErrorMessages, self).__init__("Actors cannot consume error messages.")


class InvalidTopicItemError(LeappError):
    def __init__(self, message):
        super(InvalidTopicItemError, self).__init__(message)


class InvalidTopicDefinitionError(LeappError):
    def __init__(self, message):
        super(InvalidTopicDefinitionError, self).__init__(message)


class InvalidTagDefinitionError(LeappError):
    def __init__(self, message):
        super(InvalidTagDefinitionError, self).__init__(message)


class MissingActorAttributeError(LeappError):
    def __init__(self, message):
        super(MissingActorAttributeError, self).__init__(message)


class WrongAttributeTypeError(LeappError):
    def __init__(self, message):
        super(WrongAttributeTypeError, self).__init__(message)


class ModelDefinitionError(LeappError):
    def __init__(self, message):
        super(ModelDefinitionError, self).__init__(message)


class TagFilterUsageError(LeappError):
    def __init__(self, message):
        super(TagFilterUsageError, self).__init__(message)


class CyclingDependenciesError(LeappError):
    def __init__(self, message):
        super(CyclingDependenciesError, self).__init__(message)


class UnsupportedDefinitionKindError(LeappError):
    def __init__(self, message):
        super(UnsupportedDefinitionKindError, self).__init__(message)


class ModuleNameAlreadyExistsError(LeappError):
    def __init__(self, message):
        super(ModuleNameAlreadyExistsError, self).__init__(message)


class ActorInspectionFailedError(LeappError):
    def __init__(self, message):
        super(ActorInspectionFailedError, self).__init__(message)


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
    def __init__(self, message):
        super(ActorDiscoveryExecutionError, self).__init__(message)


class UsageError(LeappError):
    def __init__(self, message):
        super(UsageError, self).__init__(message)


class CommandError(LeappError):
    def __init__(self, message):
        super(CommandError, self).__init__(message)


class CommandDefinitionError(LeappError):
    def __init__(self, message):
        super(CommandDefinitionError, self).__init__(message)


class LeappRuntimeError(LeappError):
    def __init__(self, message):
        super(LeappRuntimeError, self).__init__(message)


class StopActorExecution(Exception):
    """ This exception is used to gracefully stop execution of actor, but allows the workflow to continue. """
    def __init__(self):
        super(StopActorExecution, self).__init__()


class StopActorExecutionError(LeappError):
    """
    This exception is used to gracefully stop execution of actor and it will call
    :py:func:`leapp.actors.Actor.report_error`.
    """
    # import here to break import cycle
    from leapp.models.error_severity import ErrorSeverity

    def __init__(self, message,  severity=ErrorSeverity.ERROR, details=None):
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
