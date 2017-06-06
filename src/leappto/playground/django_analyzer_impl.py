from conf.django.replace import process_settings_file
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


__comparator_map = {
    'any_endswith': any_endswith,
    'any_contains': any_contains,
}


def find_unit_by(units, key, value, selector=None, comparator=None, lowercase=False):
    """
    
    :param units: 
    :type units: map[systemd.Unit, systemd.UnitFile]
    :param key: 
    :type key: str or any
    :param value: 
    :param selector: 
    :type selector: func
    :param comparator: 
    :type comparator: func
    :param lowercase: 
    :type lowercase: bool
    :return: 
    """
    for uf in units['unit_files']:
        for unit in uf['units']:
            k = unit[key] if not selector else selector(unit)
            if not selector and lowercase:
                k = k.lower()
            if comparator:
                if comparator(k, value):
                    yield unit
            elif value in k:
                yield unit


def find_postgresql_units(units):
    return find_unit_by(units, 'unit_name', 'postgresql', lowercase=True)


def find_django_units(units):
    return find_unit_by(units, 'exec_start', 'manage.py', comparator=any_contains)


def find_memcached_units(units):
    return find_unit_by(units, 'unit_name', 'memcached', lowercase=True)


def find_pgdata(pgsql_unit):
    key = 'PGDATA='
    vars = pgsql_unit['environment']
    for var in vars:
        if var.startswith(key):
            return var[len(key):]


def django_substitute_settings(orig_file, db_url, cache_url):
    pass


def find_settings_files(base_path):
    for root, dirs, files in walk(base_path):
        for file in files:
            if 'local_setting' in file and file[-3:] == '.py':
                yield join(root, file)


def analyze_django_units(units):
    analyzed_units = []
    for unit in units:
        manage_py = first_contains(unit['exec_start'], 'manage.py')
        data = check_output(['python', 'django_analyzer.py', manage_py])
        data_dir = dirname(manage_py)
        settings = list(find_settings_files(data_dir))
        analyzed_units.append({
            'unit': unit,
            'data': loads(data),
            'path': data_dir,
            'settings': settings,
            'deploy_settings': [
                {
                    'name': s, 
                    'detail': process_settings_file(s)
                } for s in settings
            ]
        })
    return analyzed_units


service_data = get_service_data()
django_units = list(find_django_units(service_data))
postgres_units = list(find_postgresql_units(service_data))
memcached_units = list(find_memcached_units(service_data))

data = {
    'django': analyze_django_units(django_units),
    'detail': {}
}
data['detail']['memcached'] = {
    'detail': memcached_units,
    'data_dirs': []
}
data['detail']['postgresql'] = {
    'detail': postgres_units, 
    'data_dirs': list({find_pgdata(pu) for pu in postgres_units})
}

from shutil import copyfile
for dju in data['django']:
    ds = dju['deploy_settings'][0]
    with open('artifacts/local_settings.py', 'w+') as out:
        out.write(ds['detail'])
    copyfile(ds['name'], 'artifacts/local_settings.py.original')

print(dumps(data, indent=4))
