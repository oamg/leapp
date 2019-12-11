import sys
from subprocess import check_call
from setuptools import find_packages, setup
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('leapp/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

check_call([sys.executable, 'res/schema/embed.py'])

with open('res/schema/schemas.py', 'r') as orig:
    with open('leapp/utils/schemas.py', 'w') as target:
        target.write(orig.read())

EXCLUSION = []
if sys.version_info[0] > 2:
    # Python 2 only
    EXCLUSION.append('leapp.compatpy2only')

setup(
    name='leapp',
    version=main_ns['VERSION'],
    packages=find_packages(exclude=EXCLUSION),
    install_requires=['six', 'requests'],
    entry_points='''
        [console_scripts]
        snactor=leapp.snactor:main
        leapp=leapp.cli:main

        [pytest11]
        snactor_plugin=leapp.snactor.fixture
    '''
)
