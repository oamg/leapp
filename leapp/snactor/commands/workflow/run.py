from __future__ import print_function

import leapp.workflows
import sys
from leapp.exceptions import LeappError, UsageError, CommandError
from leapp.snactor.commands.workflow import workflow
from leapp.utils.clicmd import command_arg, command_opt
from leapp.logger import configure_logger
from leapp.utils.repository import requires_repository, find_repository_basedir
from leapp.repository.scan import find_and_scan_repositories
from leapp.utils.output import report_errors, beautify_actor_exception

_LONG_DESCRIPTION = '''
Executes the given workflow.

Using --until-phase the workflow will be only executed until including
the given phase.

Using --until-actor the workflow will be only executed until including
the first occurrence of the given actor name.

For more information please consider reading the documentation at:
https://red.ht/leapp-docs
'''


@workflow.command('run', help='Execute a workflow with the given name', description=_LONG_DESCRIPTION)
@command_arg('name')
@command_opt('until-phase', help='Runs until including the given phase but then exits')
@command_opt('until-actor', help='Runs until including the given actor but then exits')
@command_opt('--whitelist-experimental', action='append', metavar='ActorName',
             help='Enables experimental actors')
@requires_repository
def cli(params):
    configure_logger()
    repository = find_and_scan_repositories(find_repository_basedir('.'), include_locals=True)
    try:
        repository.load()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.exit(1)

    wf = repository.lookup_workflow(params.name)
    if not wf:
        raise CommandError('Could not find any workflow named "{}"'.format(params.name))

    instance = wf()
    for actor_name in params.whitelist_experimental or ():
        actor = repository.lookup_actor(actor_name)
        if actor:
            instance.whitelist_experimental_actor(actor)

    with beautify_actor_exception():
        instance.run(until_phase=params.until_phase, until_actor=params.until_actor)

    report_errors(instance.errors)
