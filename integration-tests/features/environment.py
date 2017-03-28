import contextlib

def before_scenario(context, scenario):
    context.resource_manager = contextlib.ExitStack()

def after_scenario(context, scenario):
    context.resource_manager.close()
