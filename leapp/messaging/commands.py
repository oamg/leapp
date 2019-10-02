class WorkflowCommand(object):
    def __init__(self, command, arguments):
        self._command = command
        self._arguments = arguments

    def encode(self):
        return {'command': self._command, 'arguments': self._arguments}


class SkipPhasesUntilCommand(WorkflowCommand):
    COMMAND = 'skip_phases_until'

    def __init__(self, until_phase):
        super(SkipPhasesUntilCommand, self).__init__(self.COMMAND, {'until_phase': until_phase})
