import contextlib
import subprocess

def before_all(context):
    # Some steps require sudo, so for convenience in interactive use,
    # we ensure we prompt for elevated permissions immediately,
    # rather than potentially halting midway through a test
    subprocess.check_output(["sudo", "echo", "Elevated permissions needed"])

def before_scenario(context, scenario):
    context.resource_manager = contextlib.ExitStack()

def after_scenario(context, scenario):
    context.resource_manager.close()
