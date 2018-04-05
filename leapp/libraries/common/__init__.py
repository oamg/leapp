"""
:py:mod:`leapp.libraries.common` represents the import location for shared libraries that
are placed in the repository's libraries folder

Example:
      If any of the repositories has a libraries folder with a python module called module.py you can import it
      from the actor like this::

      from leapp.libraries.common import module

"""

LEAPP_BUILTIN_COMMON_INITIALIZED = False
"""Internal variable to the framework to know if the common libraries have been already initialized"""
