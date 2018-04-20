import subprocess


def reboot_system():
    subprocess.Popen(['/sbin/shutdown', '-r', 'now'])
