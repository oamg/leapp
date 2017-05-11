import functools


def _meta_receiver(cls):
    return cls.__leapp_actor_meta__

def _meta_decorator(f):
    @functools.wraps(f)
    def impl(*args, **kwargs):
        @functools.wraps(f)
        def decorator(cls):
            meta = getattr(cls, '__leapp_actor_meta__', None)
            if not meta:
                meta = cls.__leapp_actor_meta__ = {}
                cls.leapp_meta = classmethod(_meta_receiver)
            meta[f.__name__] = meta.get(f.__name__, []) + list(args)
            return cls
        return decorator
    return impl


@_meta_decorator
def ports(*ports, **kwargs):
    pass


@_meta_decorator
def config_files(*ports, **kwargs):
    pass


@_meta_decorator
def rpms(*ports, **kwargs):
    pass


@_meta_decorator
def services(*ports, **kwargs):
    pass


@_meta_decorator
def targets_services(*names, **kwargs):
    pass


@_meta_decorator
def address_links(*links, **kwargs):
    pass

def addr_link(addr, target):
    fully_qualified = '{}.{}'.format(target.__module__, target.__name__)}
    return address_links({'address': addr, 'target': fully_qualified)

