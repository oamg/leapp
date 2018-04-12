import os
import sys
from subprocess import check_call
from setuptools import find_packages, setup
from distutils.util import convert_path
from shutil import copyfile

main_ns = {}
ver_path = convert_path('leapp/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

check_call([sys.executable, 'res/schema/embed.py'])

with open('res/schema/schemas.py', 'r') as orig:
    with open('leapp/utils/schemas.py', 'w') as target:
        target.write(orig.read())

setup(
    name='leapp',
    version=main_ns['VERSION'],
    packages=find_packages(),
    install_requires=['requests', 'six'],
    entry_points='''
        [console_scripts]
        snactor=leapp.snactor:main
        leapp=leapp.cli:main
    '''
)
