from systemd import get_service_data
from subprocess import check_output
from json import loads, dumps
from os.path import dirname, join
from os import walk


def any_endswith(seq, string):
    if not seq:
        return False
    return any(s.endswith(string) for s in seq)


def first_endswith(seq, string):
    for item in seq:
        if item.endswith(string):
            return item


def any_contains(seq, string):
    if not seq:
        return False
    return any(string in s for s in seq)


def first_contains(seq, string):
    if not seq:
        return None
    for item in seq:
        if string in item:
            return item


def find_django_units(units):
    for uf in units['unit_files']:
        for unit in uf['units']:
            if any_contains(unit['exec_start'], 'manage.py'):
                yield unit


def find_settings_files(base_path):
    for root, dirs, files in walk(base_path):
        for file in files:
            if 'setting' in file and file[-3:] == '.py':
                yield join(root, file)


def analyze_django_units(units):
    analyzed_units = []
    for unit in units:
        manage_py = first_contains(unit['exec_start'], 'manage.py')
        data = check_output(['python', 'django_analyzer.py', manage_py])
        data_dir = dirname(manage_py)
        settings = find_settings_files(data_dir)
        analyzed_units.append({
            'unit': unit,
            'data': loads(data),
            'path': data_dir,
            'settings': list(settings)
        })
    return dumps(analyzed_units, indent=4)

print(analyze_django_units(find_django_units(get_service_data())))
