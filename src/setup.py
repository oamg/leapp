"""LeApp CLI and supporting services and libraries"""
# Package setup based on the PyPA example project at
# https://github.com/pypa/sampleproject/blob/master/setup.py

from codecs import open
from distutils.util import convert_path
from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

_VERSION = None
_NAME = None

# Extract the version and name from the new leappto module
with open(convert_path('leappto/version.py')) as mod:
    ns = {}
    exec(mod.read(), ns)
    _VERSION = ns['__version__']
    _NAME = ns['__pkg_name__']

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=_NAME,
    version=_VERSION,

    description='Migrate legacy application VMs into macrocontainers',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/leapp-to/leapp',

    # Author details
    author='Red Hat',
    author_email='leapp-devel@redhat.com',

    # Choose your license
    license='LGPLv2+',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',  # 2.7 only (at least for now)
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Operating System Kernels :: Linux',
    ],
    keywords='Linux containers migration',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Runtime dependencies
    install_requires=[
        "enum34",
        "libvirt-python",
        "paramiko",
        "python-nmap==0.6.1",
        "psutil==5.2.2"
    ],

    # Extras:
    #   dbus: dependencies needed to run the DBus status caching service
    #   test: dependencies needed to run the tests
    extras_require={
        'dbus': [],
        'test': [],
    },

    # No bundled package data yet
    package_data={},

    # Install `leapp-tool` command
    entry_points={
        'console_scripts': [
            'leapp-tool=leappto.cli:main',
        ],
    },
)
