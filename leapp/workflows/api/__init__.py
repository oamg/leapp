class WorkflowAPI(object):
    produces = ()
    consumes = ()
    apis = ()

    def __init__(self):
        pass

    @classmethod
    def serialize(cls):
        return {
            'name': cls.__name__,
            'module': cls.__module__,
            'consumes': [model.__name__ for model in cls.consumes],
            'produces': [model.__name__ for model in cls.produces],
            'apis': [api.__name__ for api in cls.apis]
        }
