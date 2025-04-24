import itertools
from collections import defaultdict
import sys

from leapp.exceptions import CommandError, LeappError
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.snactor.context import with_snactor_context
from leapp.utils.clicmd import command, command_arg, command_opt
from leapp.utils.repository import find_repository_basedir, requires_repository

_LONG_DESCRIPTION = '''
Outputs the graph of dependencies between actors formed by producer/consumer their relations in the DOT langauge.
The DOT language allows easy visualization of the graph.
'''


@command('show-dependencies',
         help='Print dependency graph of a workflow in the DOT language.',
         description=_LONG_DESCRIPTION)
@command_arg('workflow_name')
@command_opt('only-influencing-actor',
             metavar='ActorName',
             help='Show only actors that influence the given actor by producing messages')
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
        raise CommandError('Could not find any workflow named "{}"'.format(params.workflow_name))

    actor_of_interest = None
    if params.only_influencing_actor:
        actor_of_interest = repository.lookup_actor(params.only_influencing_actor)
        if not actor_of_interest:
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

    actors_to_include = set()
    if actor_of_interest:
        # Compute backwards reachability
        worklist = [actor_of_interest.name]
        while worklist:
            explored_actor = worklist.pop(-1)
            actors_to_include.add(explored_actor.name)

            for consumed_message in explored_actor.consumes:
                message_producer_names = dependency_graph[consumed_message.__name__]['producers']
                for producer_name in message_producer_names:
                    if producer_name in actors_to_include:
                        continue

                    producer = repository.lookup_actor(producer_name)
                    worklist.append(producer)

    # Display the dependency graph in the DOT format. We don't want to add dependencies on another library,
    # so we do the formatting ourselves since its pretty straightforward
    dot_output_lines = ['digraph LeappDependencyGraph {']

    for message, message_info in dependency_graph.items():
        for producent, consument in itertools.product(message_info['producers'], message_info['consumers']):
            # In case we show only influential actors, check that both message source and message targets
            # are to be displayed
            if actor_of_interest and not actors_to_include.issubset((producent, consument)):
                continue

            output_line = '  "{0}" -> "{1}" [label="{2}"]'.format(producent, consument, message)
            dot_output_lines.append(output_line)

    dot_output_lines.append('}')
    dot_output = '\n'.join(dot_output_lines) + '\n'
    print(dot_output, end='')
