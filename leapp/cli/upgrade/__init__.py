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
from leapp.messaging.answerstore import AnswerStore
from leapp.repository.scan import find_and_scan_repositories
from leapp.utils.audit import Execution, get_connection, get_checkpoints
from leapp.utils.clicmd import command, command_opt
from leapp.utils.output import report_errors, report_info, beautify_actor_exception, report_unsupported
from leapp.utils.report import fetch_upgrade_report_messages, generate_report_file


def archive_logfiles():
    """ Archive log files from a previous run of Leapp """
    cfg = get_config()

    if not os.path.isdir(cfg.get('files_to_archive', 'dir')):
        os.makedirs(cfg.get('files_to_archive', 'dir'))

    files_to_archive = [os.path.join(cfg.get('files_to_archive', 'dir'), f)
                        for f in cfg.get('files_to_archive', 'files').split(',')
                        if os.path.isfile(os.path.join(cfg.get('files_to_archive', 'dir'), f))]

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


def generate_report_files(context):
    """
    Generates all report files for specific leapp run (txt and json format)
    """
    cfg = get_config()
    report_txt, report_json = [os.path.join(cfg.get('report', 'dir'),
                                            'leapp-report.{}'.format(f)) for f in ['txt', 'json']]
    # fetch all report messages as a list of dicts
    messages = fetch_upgrade_report_messages(context)
    generate_report_file(messages, context, report_json)
    generate_report_file(messages, context, report_txt)


def get_cfg_files(section, cfg, must_exist=True):
    """
    Provide files from particular config section
    """
    files = []
    for file_ in cfg.get(section, 'files').split(','):
        file_path = os.path.join(cfg.get(section, 'dir'), file_)
        if not must_exist or must_exist and os.path.isfile(file_path):
            files.append(file_path)
    return files


def warn_if_unsupported(configuration):
    env = os.environ
    if env.get('LEAPP_UNSUPPORTED', '0') == '1':
        devel_vars = {k: env[k] for k in env if k.startswith('LEAPP_DEVEL_')}
        report_unsupported(devel_vars, configuration["whitelist_experimental"])


def handle_output_level(args):
    """
    Set environment variables following command line arguments.
    """
    os.environ['LEAPP_DEBUG'] = '1' if args.debug else os.environ.get('LEAPP_DEBUG', '0')
    if os.environ['LEAPP_DEBUG'] == '1' or args.verbose:
        os.environ['LEAPP_VERBOSE'] = '1'
    else:
        os.environ['LEAPP_VERBOSE'] = os.environ.get('LEAPP_VERBOSE', '0')


def prepare_configuration(args):
    """Returns a configuration dict object while setting a few env vars as a side-effect"""
    if args.whitelist_experimental:
        args.whitelist_experimental = list(itertools.chain(*[i.split(',') for i in args.whitelist_experimental]))
        os.environ['LEAPP_EXPERIMENTAL'] = '1'
    else:
        os.environ['LEAPP_EXPERIMENTAL'] = '0'
    os.environ['LEAPP_UNSUPPORTED'] = '0' if os.getenv('LEAPP_UNSUPPORTED', '0') == '0' else '1'
    configuration = {
        'debug': os.getenv('LEAPP_DEBUG', '0'),
        'verbose': os.getenv('LEAPP_VERBOSE', '0'),
        'whitelist_experimental': args.whitelist_experimental or ()
    }
    return configuration


def process_whitelist_experimental(repositories, workflow, configuration, logger=None):
    for actor_name in configuration.get('whitelist_experimental', ()):
        actor = repositories.lookup_actor(actor_name)
        if actor:
            workflow.whitelist_experimental_actor(actor)
        else:
            msg = 'No such Actor: {}'.format(actor_name)
            if logger:
                logger.error(msg)
            raise CommandError(msg)


@command('upgrade', help='Upgrades the current system to the next available major version.')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
@command_opt('reboot', is_flag=True, help='Automatically performs reboot when requested.')
@command_opt('whitelist-experimental', action='append', metavar='ActorName', help='Enables experimental actors')
@command_opt('load-answerfile', help='Path to load custom answerfile')
@command_opt('debug', is_flag=True, help='Enable debug mode', inherit=False)
@command_opt('verbose', is_flag=True, help='Enable verbose logging', inherit=False)
def upgrade(args):
    skip_phases_until = None
    context = str(uuid.uuid4())
    cfg = get_config()
    configuration = prepare_configuration(args)

    if os.getuid():
        raise CommandError('This command has to be run under the root user.')
    handle_output_level(args)

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
    process_whitelist_experimental(repositories, workflow, configuration, logger)
    warn_if_unsupported(configuration)
    with beautify_actor_exception():
        answerfile_path = cfg.get('report', 'answerfile')
        logger.info("Using answerfile at %s", answerfile_path)
        workflow.load_answerfile(answerfile_path)
        workflow.run(context=context, skip_phases_until=skip_phases_until, skip_dialogs=True)

    report_errors(workflow.errors)
    generate_report_files(context)

    cfg = get_config()

    report_files = get_cfg_files('report', cfg)
    log_files = get_cfg_files('logs', cfg)
    report_info(report_files, log_files, fail=workflow.failure)

    if workflow.failure:
        sys.exit(1)


@command('preupgrade', help='Generate preupgrade report')
@command_opt('whitelist-experimental', action='append', metavar='ActorName', help='Enables experimental actors')
@command_opt('save-answerfile', help='Path to save custom answerfile')
@command_opt('debug', is_flag=True, help='Enable debug mode', inherit=False)
@command_opt('verbose', is_flag=True, help='Enable verbose logging', inherit=False)
def preupgrade(args):
    context = str(uuid.uuid4())
    cfg = get_config()
    configuration = prepare_configuration(args)
    answerfile_path = cfg.get('report', 'answerfile')

    if os.getuid():
        raise CommandError('This command has to be run under the root user.')
    handle_output_level(args)
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
    warn_if_unsupported(configuration)
    process_whitelist_experimental(repositories, workflow, configuration, logger)
    with beautify_actor_exception():
        workflow.load_answerfile(answerfile_path)
        until_phase = 'ReportsPhase'
        logger.info('Executing workflow until phase: %s', until_phase)
        workflow.run(context=context, until_phase=until_phase, skip_dialogs=True)

    logger.info("Answerfile will be created at %s", answerfile_path)
    workflow.save_answerfile(answerfile_path)
    generate_report_files(context)
    report_errors(workflow.errors)
    report_files = get_cfg_files('report', cfg)
    log_files = get_cfg_files('logs', cfg)
    report_info(report_files, log_files, fail=workflow.failure)
    if workflow.failure:
        sys.exit(1)


@command('answer', help='Manage answerfile')
@command_opt('answerfile', help='Path to an answerfile to update')
@command_opt('section', action='append', metavar='dialog_sections',
             help='Record answer for specific section in answerfile')
def answer(args):
    """A command to manage answerfile. Updates answerfile with userchoices"""
    cfg = get_config()
    if args.section:
        args.section = list(itertools.chain(*[i.split(',') for i in args.section]))
    else:
        raise CommandError('At least one dialog section must be specified, ex. --section dialog.option=mychoice')
    try:
        sections = [tuple((dialog_option.split('.', 2) + [value]))
                    for dialog_option, value in [s.split('=', 2) for s in args.section]]
    except ValueError:
        raise CommandError("A bad formatted section has been passed. Expected format is dialog.option=mychoice")
    answerfile_path = args.answerfile or cfg.get('report', 'answerfile')
    answerstore = AnswerStore()
    answerstore.load(answerfile_path)
    for dialog, option, value in sections:
        answerstore.answer(dialog, option, value)
    not_updated = answerstore.update(answerfile_path)
    if not_updated:
        sys.stderr.write("WARNING: Only sections found in original userfile can be updated, ignoring {}\n".format(
            ",".join(not_updated)))


@command('list-runs', help='List previous Leapp upgrade executions')
def list_runs(args):  # noqa; pylint: disable=unused-argument
    contexts = fetch_all_upgrade_contexts()
    if contexts:
        for context in contexts:
            print('Context ID: {} - time: {} - details: {}'.format(context[0], context[1], json.loads(context[2])),
                  file=sys.stdout)
    else:
        raise CommandError('No previous run found!')
