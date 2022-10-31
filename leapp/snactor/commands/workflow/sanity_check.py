from __future__ import print_function

import sys

from leapp.exceptions import CommandError, LeappError
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.commands.workflow import workflow
from leapp.utils.clicmd import command_arg, command_opt
from leapp.utils.output import Color
from leapp.utils.repository import find_repository_basedir, requires_repository

_DESCRIPTION = 'The following messages are attempted to be consumed before they are produced: {}'
_LONG_DESCRIPTION = '''
Perform workflow sanity checks

- check whether there is a message in the given workflow which is attempted to be consumed before it was produced
  --ignore <MODEL> can be used to specify one or multiple times to ignore the above condition
  --ignorefile <PATH to ignore file> can be used to specify a file to load a list of ignored models. The list shall be
    new line separated. Lines beginning with # are considered comments.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


def print_fail(error):
    print('{red}FAIL: {error}{reset}'.format(red=Color.red, error=error, reset=Color.reset), file=sys.stderr, end='\n')


def _ignore_file_content(path):
    if not path:
        return []
    with open(path) as f:
        return [line.strip() for line in f.read().split('\n') if line.strip() and not line.strip().startswith('#')]


@workflow.command('sanity-check', help='Perform workflow sanity checks', description=_LONG_DESCRIPTION)
@command_arg('name')
@command_opt('ignore', metavar='<MODEL>', action='append', help='Models to ignore in the sanity check.')
@command_opt('ignorefile', metavar='<PATH to ignore file>', help='File with a list of model names to ignore.')
@requires_repository
def cli(params):
    ignored_models = set(params.ignore or []) | set(_ignore_file_content(params.ignorefile))
    configure_logger()
    repository = find_and_scan_repositories(find_repository_basedir('.'), include_locals=True)
    try:
        repository.load()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.stderr.write('\n')
        sys.exit(1)

    wf = repository.lookup_workflow(params.name)
    if not wf:
        raise CommandError('Could not find any workflow named "{}"'.format(params.name))

    instance = wf()
    produced_late = set(instance.initial).intersection(set(instance.produces))
    produced_late_names = [model.__name__ for model in produced_late if model.__name__ not in ignored_models]
    if produced_late_names:
        print_fail(_DESCRIPTION.format(' '.join([m.__name__ for m in produced_late])))
        sys.exit(1)
