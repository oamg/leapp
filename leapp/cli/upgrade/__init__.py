from leapp.utils.clicmd import command, command_opt


@command('upgrade', help='')
@command_opt('resume', is_flag=True, help='Continue the last execution after it was stopped (e.g. after reboot)')
def upgrade(args):
    pass
