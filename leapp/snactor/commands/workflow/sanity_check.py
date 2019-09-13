from __future__ import print_function
import sys

from leapp.exceptions import LeappError, CommandError
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.commands.workflow import workflow
from leapp.utils.clicmd import command_arg
from leapp.utils.repository import requires_repository, find_repository_basedir

_DESCRIPTION = 'The following messages are attempted to be consumed before they are produced: {}'
_LONG_DESCRIPTION = '''
Perform workflow sanity checks

- check whether there is a message in the given workflow which is attempted to be consumed before it was produced

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@workflow.command('sanity-check', help='Perform workflow sanity checks', description=_LONG_DESCRIPTION)
@command_arg('name')
@requires_repository
def cli(params):
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
    if produced_late:
        print(_DESCRIPTION.format(' '.join([m.__name__ for m in produced_late])), file=sys.stderr, end='\n')
        sys.exit(1)
