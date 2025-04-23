import itertools
from collections import defaultdict
import sys

from leapp.exceptions import CommandError, LeappError
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.context import with_snactor_context
from leapp.utils.clicmd import command, command_arg
from leapp.utils.repository import find_repository_basedir, requires_repository

_LONG_DESCRIPTION = '''
Outputs the graph of dependencies between actors formed by producer/consumer their relations in the DOT langauge.
The DOT language allows easy visualization of the graph.
'''


@command('show-dependencies',
         help='Print dependency graph of a workflow in the DOT language.',
         description=_LONG_DESCRIPTION)
@command_arg('workflow_name')
@requires_repository
@with_snactor_context
def cli(params):
    configure_logger()
    repository = find_and_scan_repositories(find_repository_basedir('.'), include_locals=True)
    try:
        repository.load()
    except LeappError as exc:
        sys.stderr.write(exc.message)
        sys.stderr.write('\n')
        sys.exit(1)

    workflow = repository.lookup_workflow(params.workflow_name)
    if not workflow:
        raise CommandError('Could not find any workflow named "{}"'.format(params.name))

    workflow_instance = workflow()

    # Information about message consuments and producers:
    dependency_graph = defaultdict(lambda: {'producers': set(), 'consumers': set()})

    for staged_phase in workflow_instance.phase_actors:
        # staged_phase = ('name' <str>, 'Before' <PhaseActors>, 'Main' <PhaseActors>, 'After' <PhaseActors>)
        before_stage, main_stage, after_stage = staged_phase[1:]

        for actor in itertools.chain(before_stage.actors, main_stage.actors, after_stage.actors):
            for consumed_message in actor.consumes:
                dependency_graph[consumed_message.__name__]['consumers'].add(actor.name)
            for produced_message in actor.produces:
                dependency_graph[produced_message.__name__]['producers'].add(actor.name)

    # Display the dependency graph in the DOT format. We don't want to add dependencies on another library,
    # so we do the formatting ourselves since its pretty straightforward
    dot_output_lines = ['digraph LeappDependencyGraph {']

    for message, message_info in dependency_graph.items():
        for producent, consument in itertools.product(message_info['producers'], message_info['consumers']):
            output_line = '  "{0}" -> "{1}" [label="{2}"]'.format(producent, consument, message)
            dot_output_lines.append(output_line)

    dot_output_lines.append('}')
    dot_output = '\n'.join(dot_output_lines) + '\n'
    print(dot_output, end='')
