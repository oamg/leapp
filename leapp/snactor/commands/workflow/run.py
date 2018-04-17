from __future__ import print_function

import leapp.workflows
from leapp.snactor.commands.workflow import workflow
from leapp.utils.clicmd import command_arg, command_opt
from leapp.logger import configure_logger
from leapp.utils.project import requires_project, find_project_basedir
from leapp.repository.scan import scan_repo


@workflow.command('run', help='Execute a workflow with the given name')
@command_arg('name')
@command_opt('until-phase', help='Runs until including the given phase but then exits')
@command_opt('until-actor', help='Runs until including the given actor but then exits')
@requires_project
def cli(params):
    configure_logger()
    repository = scan_repo(find_project_basedir('.'))
    repository.load()
    for wf in leapp.workflows.get_workflows():
        if wf.name.lower() == params.name.lower():
            wf().run(until_phase=params.until_phase, until_actor=params.until_actor)
