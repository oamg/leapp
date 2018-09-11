import ast
import functools
import itertools
import os


def print_section(data, section, pivot):
    "Print a section of obtained data"
    type_data = data[section]
    print('{}'.format(section.capitalize()))
    for td in type_data:
        fp = format_file_path(pivot, td['file'])
        first_part = '  - {}({})'.format(td['name'], ', '.join(td['bases']))
        pad = '.' * (60 - len(first_part))
        print('{} {} {}'.format(first_part, pad, fp))
    print('')


def format_file_path(pivot, path):
    "Format path as relative to a pivot"
    if not pivot or pivot == '.':
        pivot = os.getcwd()
    return os.path.relpath(path, pivot)


def get_candidate_files(start='.'):
    "Find all .py files in a directory tree"
    for root, unused, files in os.walk(start):
        for f in files:
            if not f.endswith('py'):
                continue
            yield os.path.join(root, f)


def ast_parse_file(file):
    "Parse a python file and return tuple (ast, filename)"
    with open(file, mode='r') as fp:
        try:
            return ast.parse(fp.read(), file), file
        except Exception:
            return None, file


def get_base_classes(bases, via):
    "Get base classes of a type, only direct names are supported currently"
    bases_set = set()
    errors = []
    for base in bases:
        if isinstance(base, ast.Name):
            bases_set.add(base.id)
        else:
            errors.append('Unknown base: {} via {}'.format(base.__class__.__name__, via))
    return bases_set, errors


def inspect(tree_file, collected_types={}, type_infos={}):
    "Inspect and collect data from AST tree"
    tree, file = tree_file
    if not tree:
        return ['Unable to parse: {}'.format(file)]
    errors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_classes, err = get_base_classes(node.bases, file)
            errors += err

            if base_classes & collected_types['models']:
                collected_types['models'].add(node.name)
                type_infos['models'].append({
                    'name': node.name,
                    'bases': list(base_classes),
                    'file': file
                })
            if base_classes & collected_types['actors']:
                collected_types['actors'].add(node.name)
                type_infos['actors'].append({
                    'name': node.name,
                    'bases': list(base_classes),
                    'file': file
                })
            if base_classes & collected_types['tags']:
                collected_types['tags'].add(node.name)
                type_infos['tags'].append({
                    'name': node.name,
                    'bases': list(base_classes),
                    'file': file
                })
    return errors


def safe_discover(pivot):
    # Here we collect all the types that inherit from Model/Actor/Tag types
    # so that we can use this dict as a lookup for deeper search to support
    # use cases like:
    #
    # class FirstOrderModel(Model):
    #     pass
    #
    # class SecondOrderModel(FirstOrderModel):
    #     pass
    #
    collected_types = {
        'models': set(['Model']),
        'actors': set(['Actor']),
        'tags': set(['Tag'])
    }
    type_infos = {
        'models': [],
        'actors': [],
        'tags': []
    }

    inspector = functools.partial(
        inspect,
        collected_types=collected_types,
        type_infos=type_infos
    )

    errors = filter(None, map(inspector, map(ast_parse_file, get_candidate_files(pivot))))
    flat_errors = list(itertools.chain(*errors))

    print_section(type_infos, 'actors', pivot)
    print_section(type_infos, 'models', pivot)
    print_section(type_infos, 'tags', pivot)
    if flat_errors:
        print('Errors:')
        print('\n'.join(flat_errors))
