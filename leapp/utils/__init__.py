import subprocess


def reboot_system():
    subprocess.Popen(['/sbin/shutdown', '-r', 'now'])


def get_api_models(actor, what):
    """
    Used to retrieve the full list of models including the ones defined by WorkflowAPIs used by the actor.

    :param what: A string which either is 'consumes' or 'produces'
    :type what: str
    :param actor: Actor type/instance or ActorDefinition instance to retrieve the information from
    :type actor: Actor or ActorDefinition
    :return: Tuple of all produced or consumed models as specified by actor and APIs used by the actor.
    """

    def _enforce_tuple(x):
        if not isinstance(x, tuple):
            return (x,)
        return x

    def _do_get(api):
        result = _enforce_tuple(getattr(api, what, ()))
        for a in _enforce_tuple(api.apis or ()):
            result = result + _do_get(a)
        return result
    return tuple(set(_do_get(actor)))
