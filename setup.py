from setuptools import find_packages, setup
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('leapp/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

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
