class Policies(object):
    class Errors(object):
        class FailPhase(object):
            pass

        class FailImmediately(object):
            pass

        class ReportOnly(object):
            pass

    class Retry(object):
        class Actor(object):
            pass

        class Phase(object):
            pass

        class Disabled(object):
            pass

    def __init__(self, error=Errors.ReportOnly, retry=Retry.Disabled):
        self.error = error
        self.retry = retry
