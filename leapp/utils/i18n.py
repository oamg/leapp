import leapp.compat

import locale
import os
import logging


def setup_locale():
    try:
        leapp.compat.setlocale(locale.LC_ALL)
    except locale.Error:
        logging.getLogger('leapp.i18n').error('Failed to set locale, defaulting to C', exc_info=True)
        os.environ['LC_ALL'] = 'C'
        leapp.compat.setlocale(locale.LC_ALL, 'C')


def translation(domain):
    setup_locale()
    return leapp.compat.gettext_setup(
        leapp.compat.gettext.translation(domain, fallback=True))


def install_translation_for_actor(actor):
    if actor.text_domain:
        globals()['__builtins__']['_'], globals()['__builtins__']['P_'] = translation(actor.text_domain)


_, P_ = translation(os.environ.get('LEAPP_DEFAULT_TEXTDOMAIN', 'leapp'))

globals()['__builtins__']['_'], globals()['__builtins__']['P_'] = _, P_
