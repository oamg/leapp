import functools


_REGISTRY = set()


def registry(mapped=False):
    return _REGISTRY if not mapped else {_fq(s): s for s in _REGISTRY}


def _meta_receiver(cls):
    return cls.__leapp_actor_meta__


def _meta_init(cls):
    meta = getattr(cls, '__leapp_actor_meta__', None)
    if not meta:
        _REGISTRY.add(cls)
        meta = cls.__leapp_actor_meta__ = {}
        cls.leapp_meta = classmethod(_meta_receiver)
    return meta


def _meta_decorator(f):
    @functools.wraps(f)
    def impl(*args, **kwargs):
        @functools.wraps(f)
        def decorator(cls):
            meta = _meta_init(cls)
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


def _fq(target):
    return '{}.{}'.format(target.__module__, target.__name__)


def addr_link(addr, target, args=()):
    return address_links({'address': addr, 'target': _fq(target), 'arguments': list(args)})


@_meta_decorator
def require_links(*links, **kwargs):
    pass


def force_host_networking_to(target):
    requires_host_networking(target)
    def wrapper(cls):
        return cls
    return wrapper


def requires_host_networking(cls):
    meta = _meta_init(cls)
    meta['requires-host-networking'] = True
    return cls


def require_link(target):
    return require_links({'target': _fq(target)})


@_meta_decorator
def directories(*spec, **kwargs):
    pass


def directory(path, user='root', group='root', mode='0755', **kwargs):
    return directories(dict(path=path, user=user, group=group, mode=mode), **kwargs)


@_meta_decorator
def users(*users, **kwargs):
    pass
