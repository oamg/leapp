from __future__ import print_function
import itertools
import json
import os
import shutil
import sys
import tarfile
import uuid
from datetime import datetime

from leapp.config import get_config
from leapp.exceptions import CommandError, LeappError
from leapp.logger import configure_logger
from leapp.repository.scan import find_and_scan_repositories
from leapp.utils.audit import Execution, get_connection, get_checkpoints
from leapp.utils.clicmd import command, command_opt
from leapp.utils.output import report_errors, report_info, beautify_actor_exception
from leapp.utils.report import fetch_upgrade_report_messages
import leapp.reporting


def archive_logfiles():
    """ Archive log files from a previous run of Leapp """
    cfg = get_config()

    if not os.path.isdir(cfg.get('logs', 'dir')):
        os.makedirs(cfg.get('logs', 'dir'))

    files_to_archive = [os.path.join(cfg.get('logs', 'dir'), f)
                        for f in cfg.get('logs', 'files').split(',')
                        if os.path.isfile(os.path.join(cfg.get('logs', 'dir'), f))]

    if not os.path.isdir(cfg.get('archive', 'dir')):
        os.makedirs(cfg.get('archive', 'dir'))

    if files_to_archive:
        if os.path.isdir(cfg.get('debug', 'dir')):
            files_to_archive.append(cfg.get('debug', 'dir'))

        now = datetime.now().strftime('%Y%m%d%H%M%S')
        archive_file = os.path.join(cfg.get('archive', 'dir'), 'leapp-{}-logs.tar.gz'.format(now))

        with tarfile.open(archive_file, "w:gz") as tar:
            for file_to_add in files_to_archive:
                tar.add(file_to_add)
                if os.path.isdir(file_to_add):
                    shutil.rmtree(file_to_add, ignore_errors=True)
                try:
                    os.remove(file_to_add)
                except OSError:
                    pass
            # leapp_db is not in files_to_archive to not have it removed
            if os.path.isfile(cfg.get('database', 'path')):
                tar.add(cfg.get('database', 'path'))


def load_repositories_from(name, repo_path, manager=None):
    if get_config().has_option('repositories', name):
        repo_path = get_config().get('repositories', name)
    return find_and_scan_repositories(repo_path, manager=manager)


def load_repositories():
    manager = load_repositories_from('repo_path', '/etc/leapp/repo.d/', manager=None)
    manager.load()
    return manager


def fetch_last_upgrade_context():
    """
    :return: Context of the last execution
    """
    with get_connection(None) as db:
        cursor = db.execute(
            "SELECT context, stamp, configuration FROM execution WHERE kind = 'upgrade' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row[0], json.loads(row[2])
    return None, {}


def fetch_all_upgrade_contexts():
    """
    :return: All upgrade execution contexts
    """
    with get_connection(None) as db:
        cursor = db.execute(
            "SELECT context, stamp, configuration FROM execution WHERE kind = 'upgrade' ORDER BY id DESC")
        row = cursor.fetchall()
        if row:
            return row
    return None


def get_last_phase(context):
    checkpoints = get_checkpoints(context=context)
    if checkpoints:
        return checkpoints[-1]['phase']


def check_env_and_conf(env_var, conf_var, configuration):
    """
    Checks whether the given environment variable or the given configuration value are set to '1'
    """
    return os.getenv(env_var, '0') == '1' or configuration.get(conf_var, '0') == '1'


@command('upgrade', help='Upgrades the current system to the next available major version.')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
@command_opt('reboot', is_flag=True, help='Automatically performs reboot when requested.')
@command_opt('whitelist-experimental', action='append', metavar='ActorName',
             help='Enables experimental actors')
def upgrade(args):
    if os.getuid():
        raise CommandError('This command has to be run under the root user.')

    if args.whitelist_experimental:
        args.whitelist_experimental = list(itertools.chain(*[i.split(',') for i in args.whitelist_experimental]))
    skip_phases_until = None
    context = str(uuid.uuid4())
    configuration = {
        'debug': os.getenv('LEAPP_DEBUG', '0'),
        'verbose': os.getenv('LEAPP_VERBOSE', '0'),
        'whitelist_experimental': args.whitelist_experimental or ()
    }
    if args.resume:
        context, configuration = fetch_last_upgrade_context()
        if not context:
            raise CommandError('No previous upgrade run to continue, remove `--resume` from leapp invocation to'
                               'start a new upgrade flow')
        os.environ['LEAPP_DEBUG'] = '1' if check_env_and_conf('LEAPP_DEBUG', 'debug', configuration) else '0'

        if os.environ['LEAPP_DEBUG'] == '1' or check_env_and_conf('LEAPP_VERBOSE', 'verbose', configuration):
            os.environ['LEAPP_VERBOSE'] = '1'
        else:
            os.environ['LEAPP_VERBOSE'] = '0'

        skip_phases_until = get_last_phase(context)
        logger = configure_logger()
    else:
        e = Execution(context=context, kind='upgrade', configuration=configuration)
        e.store()
        archive_logfiles()
        logger = configure_logger('leapp-upgrade.log')
    os.environ['LEAPP_EXECUTION_ID'] = context

    if args.resume:
        logger.info("Resuming execution after phase: %s", skip_phases_until)
    try:
        repositories = load_repositories()
    except LeappError as exc:
        raise CommandError(exc.message)
    workflow = repositories.lookup_workflow('IPUWorkflow')(auto_reboot=args.reboot)
    for actor_name in configuration.get('whitelist_experimental', ()):
        actor = repositories.lookup_actor(actor_name)
        if actor:
            workflow.whitelist_experimental_actor(actor)
        else:
            msg = 'No such Actor: {}'.format(actor_name)
            logger.error(msg)
            raise CommandError(msg)
    with beautify_actor_exception():
        workflow.run(context=context, skip_phases_until=skip_phases_until)

    report_errors(workflow.errors)

    if workflow.failure:
        sys.exit(1)


@command('preupgrade', help='Generate preupgrade report')
@command_opt('whitelist-experimental', action='append', metavar='ActorName',
             help='Enables experimental actors')
def preupgrade(args):
    if os.getuid():
        raise CommandError('This command has to be run under the root user.')

    if args.whitelist_experimental:
        args.whitelist_experimental = list(itertools.chain(*[i.split(',') for i in args.whitelist_experimental]))
    context = str(uuid.uuid4())
    configuration = {
        'debug': os.getenv('LEAPP_DEBUG', '0'),
        'verbose': os.getenv('LEAPP_VERBOSE', '0'),
        'whitelist_experimental': args.whitelist_experimental or ()
    }
    e = Execution(context=context, kind='preupgrade', configuration=configuration)
    e.store()
    archive_logfiles()
    logger = configure_logger('leapp-preupgrade.log')
    os.environ['LEAPP_EXECUTION_ID'] = context

    try:
        repositories = load_repositories()
    except LeappError as exc:
        raise CommandError(exc.message)
    workflow = repositories.lookup_workflow('IPUWorkflow')()
    for actor_name in configuration.get('whitelist_experimental', ()):
        actor = repositories.lookup_actor(actor_name)
        if actor:
            workflow.whitelist_experimental_actor(actor)
        else:
            msg = 'No such Actor: {}'.format(actor_name)
            logger.error(msg)
            raise CommandError(msg)
    with beautify_actor_exception():
        until_phase = 'ReportsPhase'
        logger.info('Executing workflow until phase: %s', until_phase)
        workflow.run(context=context, until_phase=until_phase)

    report_errors(workflow.errors)

    report_txt, report_json = [os.path.join(get_config().get('report', 'dir'),
                                            'leapp-report.{}'.format(f)) for f in ['txt', 'json']]
    report_info([report_txt, report_json], fail=workflow.errors)
    # fetch all report messages as a list of dicts
    messages = fetch_upgrade_report_messages(context)
    with open(report_json, 'w+') as f:
        json.dump({'entries': messages}, f, indent=2)
    if workflow.failure:
        sys.exit(1)


@command('list-runs', help='List previous Leapp upgrade executions')
def list_runs(args):  # noqa; pylint: disable=unused-argument
    contexts = fetch_all_upgrade_contexts()
    if contexts:
        for context in contexts:
            print('Context ID: {} - time: {} - details: {}'.format(context[0], context[1], json.loads(context[2])),
                  file=sys.stdout)
    else:
        raise CommandError('No previous run found!')
