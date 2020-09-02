import errno
import os
import tarfile

from leapp.exceptions import CommandError


def init_phase_logs(phase_logs_archive, logger=None):
    """
    Initialize an archive for storing logs that get backed up after each phase.
    If the path already contains a file, the file is deleted.

    :param phase_logs_archive: Path at which the archive is created.
    """
    if logger:
        logger.info('Initializing archive at {}'.format(phase_logs_archive))

    if os.path.exists(phase_logs_archive):
        if logger:
            logger.info('File already exists at {}, deleting'.format(phase_logs_archive))
        try:
            os.remove(phase_logs_archive)
        except OSError as e:
            if e.errno == errno.EISDIR:
                raise CommandError('Error: {}: Is a directory'.format(phase_logs_archive))
            else:
                raise e

    if not phase_logs_archive.endswith('.tar.gz'):
        if logger:
            logger.warn('Warning: {} does not end with ".tar.gz"'.format(phase_logs_archive))

    with tarfile.open(phase_logs_archive, mode='x:gz') as tarball:  # noqa: F841
        pass


def add_phase_logs(phase_logs_archive, phase_logs, phase, logger=None):
    """
    Add defined phase logs to the archive, if they exist.

    :param phase_logs_archive: Path to an existing archive.
    :param phase_logs: A list of paths to files to be archived, mapped to their archival name prefixes.
    :param phase: The last finished phase.
    """

    # might break alphabetical order of files if there's more than 100 phases one day
    phasenum = '{:02d}'.format(phase.get_index())
    phasename = phase.name().lower()

    with tarfile.open(phase_logs_archive, mode='x:gz') as tarball:
        for log in phase_logs:
            if os.path.exists(log):
                arcname = "{}-{}-{}".format(os.path.basename(log), phasenum, phasename)
                if logger:
                    logger.info('Archiving {} as {}'.format(log, arcname))
                tarball.add(log, arcname=arcname)
            elif logger:
                logger.info('{} does not exist, skipping'.format(log))
