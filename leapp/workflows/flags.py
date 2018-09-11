class Flags(object):
    restart_after_phase = False
    request_restart_after_phase = False

    def __init__(self, request_restart_after_phase=False, restart_after_phase=False):
        self.request_restart_after_phase = request_restart_after_phase
        self.restart_after_phase = restart_after_phase

    def serialize(self):
        """
        :return: Serialized data of phase flags
        """
        return {
            'restart_after_phase': self.restart_after_phase,
            'request_restart_after_phase': self.request_restart_after_phase
        }
