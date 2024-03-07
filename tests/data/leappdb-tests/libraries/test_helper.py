import os
import json


def log_execution(actor):
    with open(os.environ['LEAPP_TEST_EXECUTION_LOG'], 'a+') as f:
        f.write(json.dumps(dict(name=actor.name, class_name=type(actor).__name__)) + '\n')
