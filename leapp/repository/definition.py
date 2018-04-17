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
    TESTS = _Kind('tests')

    REPO_WHITELIST = (ACTOR, MODEL, TOPIC, TAG, WORKFLOW, TOOLS, LIBRARIES, FILES)
    ACTOR_WHITELIST = (TOOLS, LIBRARIES, FILES, TESTS)
