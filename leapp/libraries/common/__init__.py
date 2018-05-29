"""
:py:mod:`leapp.libraries.common` represents an import location for shared libraries that
are placed in the repository's libraries folder.

Example:
      If any of the repositories has a libraries folder with a module.py python module, import it
      from the actor like this::

      from leapp.libraries.common import module

"""

LEAPP_BUILTIN_COMMON_INITIALIZED = False
"""Internal variable to the framework to inform if the common libraries have been already initialized"""
