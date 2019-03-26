"""
Functions that allow gather information about the current configuration.
"""
import os


def is_debug():
    """
    Returns True if the LEAPP_DEBUG environment variable is set to '1'.
    """
    return os.getenv('LEAPP_DEBUG', '0') == '1'


def is_verbose():
    """
    Returns True if either the LEAPP_DEBUG or the LEAPP_VERBOSE environment variable is set to '1'.
    """
    return os.getenv('LEAPP_DEBUG', '0') == '1' or os.getenv('LEAPP_VERBOSE', '0') == '1'
