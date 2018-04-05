import os
import sys

from leapp.snactor.commands.workflow import workflow
from leapp.utils.clicmd import command_arg, command_opt
from leapp.snactor.utils import find_project_basedir, requires_project, make_class_name, make_name


@workflow.command('new', help='Creates a new workflow with the given name')
@command_arg('name')
@command_opt('short-name', short_name='s')
@command_opt('class-name', short_name='c')
@requires_project
def cli(args):
    class_name = args.class_name
    short_name = args.short_name
    name = args.name
    base_dir = find_project_basedir('.')
    workflows_dir = os.path.join(base_dir, 'workflows')

    class_name = class_name or make_class_name(name)
    short_name = short_name or make_name(name)

    if not os.path.exists(workflows_dir):
        os.mkdir(workflows_dir)

    workflow_path = os.path.join(workflows_dir, make_name(name) + '.py')
    if not os.path.exists(workflow_path):
        with open(workflow_path, 'w') as f:
            f.write("""from leapp.workflows import Workflow
from leapp.workflows.phases import Phase
from leapp.workflows.flags import Flags
from leapp.workflows.filters import Filter
from leapp.workflows.tagfilters import TagFilter
from leapp.workflows.policies import Policies
from leapp.tags import {workflow_class}Tag


class {workflow_class}Workflow(Workflow):
    name = '{workflow_name}'
    tag =  {workflow_class}Tag
    short_name = '{workflow_short_name}'
    description = '''No description has been provided for the {workflow_name} workflow.'''

    # Template for phase definition - The order in which the phase classes are defined
    # within the Workflow class represents the execution order
    #
    # class PhaseName(Phase):
    #    name = 'phase_name'
    #    filter = TagFilter(PhaseTag)
    #    policies = Policies(Policies.Errors.FailPhase,
    #                        Policies.Retry.Phase)
    #    flags = Flags()
""".format(workflow_name=name, workflow_class=class_name, workflow_short_name=short_name))
    sys.stdout.write("New workflow {} has been created in {}\n".format(class_name,
                                                                       os.path.realpath(workflow_path)))
