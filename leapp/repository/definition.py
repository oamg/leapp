class DefinitionKind(object):
    """
    Represents all known repository resources in Leapp.
    """
    class _Kind(object):
        def __init__(self, kind):
            self.name = kind

    ACTOR = _Kind('actor')
    MODEL = _Kind('model')
    TOPIC = _Kind('topic')
    TAG = _Kind('tag')
    WORKFLOW = _Kind('workflow')
    LIBRARIES = _Kind('libraries')
    TOOLS = _Kind('tools')
    FILES = _Kind('files')
    CONFIGS = _Kind('configs')
    TESTS = _Kind('tests')
    API = _Kind('api')

    REPO_WHITELIST = (ACTOR, API, MODEL, TOPIC, TAG, WORKFLOW, TOOLS, LIBRARIES, FILES, CONFIGS)
    ACTOR_WHITELIST = (TOOLS, LIBRARIES, FILES, CONFIGS, TESTS)
