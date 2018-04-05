from __future__ import print_function
import json
import sys

import leapp.workflows
from leapp.snactor.commands.workflow import workflow
from leapp.utils.clicmd import command_arg
from leapp.snactor.utils import requires_project, load_all_from, find_project_basedir


separator = (type('Fake', (object,), {'name': '=============='})(),)


def names(p):
    return [_.name for a in p for _ in (separator + a.actors + separator if a.actors else ())]


@workflow.command('dump')
@command_arg('name')
@requires_project
def cli(args, extra):
    load_all_from(find_project_basedir('.'))
    wf = leapp.workflows.IPUWorkflow()
    print(wf.initial, wf.consumes, wf.produces)
    json.dump(names(wf.phase_actors), sys.stdout, indent=2)
    sys.stdout.write('\n')
