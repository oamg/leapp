from helpers import make_repository_dir_fixture


# NOTE(ivasilev) Assigning a fixture generated that way to some variable is a necessary prerequisite for it to be
# discovered by pylint
repodir_fixture = make_repository_dir_fixture(name='repository_dir', scope='session')
