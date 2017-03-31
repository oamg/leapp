import yaml, os, sys
from collections import defaultdict


if len(sys.argv) < 2:
    _target_dir = '.'
else:
    _target_dir = sys.argv[1]

_rows, _columns = list(map(int, os.popen('stty size', 'r').read().split()))
_task_cache = defaultdict(list)


def compare_dictionaries(a, b, print_on_inequality=False):
    """ Performs `unstable` comparison of two dictionaries (order of 
        elements doesn't matter) by casting ordered POD types to 
        frozenset
    """

    def mapper(item):
        if isinstance(item, list):
            return frozenset(map(mapper, item))
        if isinstance(item, dict):
            return frozenset({mapper(k): mapper(v) for k, v in item.items()}.items())
        return item

    mapped_a = mapper(a)
    mapped_b = mapper(b)
    res = mapped_a == mapped_b

    if not res and print_on_inequality:
        print(json.dumps(a, sort_keys=True, separators=(',', ': '), indent=2), file=sys.stderr)
        print(json.dumps(b, sort_keys=True, separators=(',', ': '), indent=2), file=sys.stderr)

    return res


def check_task(f, data):
    """ Check the task `data` against our task cache

    """
    if not data:
        return

    for task in data:
        if len(task) == 1 and 'include' in task:
            continue
        try:
            _task_cache[task['name']] += [f]
        except KeyError:
            print('Task without name: ', task)


def report():
    """ Print out nice (de)duplication status report

    """
    nondup, dup = [], []
    for k, v in _task_cache.items():
        if len(v) > 1:
            dup.append((k, v))
        else:
            nondup.append((k, v))

    print('Unique tasks:')
    print('='*_columns)
    for k, v in nondup:
        print('  - "{}"\n    {}'.format(k, v[0][2:]))
    print('='*_columns)
    print('')

    print('Duplicate tasks:')
    print('='*_columns)
    for k, v in dup:
        print('  - "{}"\n    {}'.format(k, "\n    ".join([x[2:] for x in v])))
        print('')
    print('='*_columns)

for root, dirs, files in os.walk(_target_dir):
    path = root.split(os.sep)
    for file in files:
        full_path = os.path.join(root, file)
        if '/tasks/' in full_path and full_path.endswith('yml'):
            data = yaml.load(open(full_path, 'r'))
            check_task(full_path, data)

report()
