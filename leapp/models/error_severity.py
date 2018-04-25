class ErrorSeverity(object):
    FATAL = 'fatal'
    ERROR = 'error'
    WARNING = 'warning'

    ALLOWED_VALUES = (FATAL, ERROR, WARNING)

    @classmethod
    def validate(cls, value):
        return value in cls.ALLOWED_VALUES
