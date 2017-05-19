#!/bin/python2


class ResourceType(object):
    (Invalid, File, Directory, NetworkSocket, UnixSocket) = range(5)


# Owns Socket
class Endpoint(object):
    def __init__(self, socket):
        self._socket = socket

    @property
    def socket(self):
        return self._socket


# Maps Endpoint <-> Endpoint communication
class Connection(object):
    def __init__(self, ep_src, ep_dst):
        self._src = ep_src
        self._dst = ep_dst

    @property
    def source(self):
        return self._src

    @property
    def destination(self):
        return self._dst


class Resource(object):
    def __init__(self):
        pass

    @property
    def resource_type(self):
        return None


class Actor(object):
    def __init__(self):
        self._resources = []
        self._connections = []

    @property
    def resources(self):
        return self._resources

    @property
    def connections(self):
        return self._connections


class Service(Actor):
    def __init__(self):
        pass
