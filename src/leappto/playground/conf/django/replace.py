import argparse
import ast
import astor
import os
import sys


def generate_import_os():
    """ Generates `import os` statement

    """
    return ast.Import(
        names=[ast.alias(name='os', asname=None)]
    )


def check_os_imports(tree):
    """ Inspect top level import for `import os`

    """
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name == 'os':
                    return True
        #TODO: Add support for from .. import ... and aliased imports
        #elif isinstance(node, ast.ImportFrom):
        #    if node.module == 'os':
        #        for name in node.names:
        #            if name.name == 'getenv' and name.asname is None:
        #                return True

    return False


def generate_host_var(service_name, default, var_prefix):
    """ Generate code for parsing service information from env. variables
        into a single variable:

            {var_prefix}_HOST - ip:port

        Note that this code currently skips the initial part of the content
        of the env. variable - either 'udp://' or 'tcp://', which,
        in terms of *service discovery* is just a noise.

    """
    return ast.Assign(
        targets=[
            ast.Name(id=var_prefix + '_HOST')
        ],
        value=ast.Subscript(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='os'),
                    attr='getenv'
                ),
                args=[ast.Str(s=service_name), ast.Str(s=default)],
                keywords=[],
                starargs=None,
                kwargs=None
            ),
            slice=ast.Slice(lower=ast.Num(n=6), upper=None, step=None)
        )
    )


def generate_host_port_vars(service_name, default, var_prefix):
    """ Generate code for parsing service information from env. variables
        into two variables:

            {var_prefix}_HOST - containing the IP/Hostname 
            {var_prefix}_PORT - containing the Port

        Note that this code currently skips the initial part of the content
        of the env. variable - either 'udp://' or 'tcp://', which,
        in terms of *service discovery* is just a noise.

    """
    return ast.Assign(
        targets=[
            ast.Tuple(elts=[
                ast.Name(id=var_prefix + '_HOST'),
                ast.Name(id=var_prefix + '_PORT')
            ])
        ],
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Subscript(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='os'),
                            attr='getenv'
                        ),
                        args=[ast.Str(s=service_name), ast.Str(s=default)],
                        keywords=[],
                        starargs=None,
                        kwargs=None
                    ),
                    slice=ast.Slice(lower=ast.Num(n=6), upper=None, step=None)
                ),
                attr='rsplit'
            ),
            args=[ast.Str(s=':'), ast.Num(n=1)],
            keywords=[],
            starargs=None,
            kwargs=None
        )
    )


def find_key(keys, key):
    """ Find index of string `key` in `keys`, and only take into
        account string keys, not arbitrary stuff overriding the
        `__hash__` method

    """
    for i, k in enumerate(keys):
        # We can only work with string based keys
        # for now
        if not isinstance(k, ast.Str):
            continue
        if k.s == key:
            return i


class ValueEnvTransformer(ast.NodeTransformer):
    """ AST Transformer to turn immediate string value into
        a variable reference

    """
    def __init__(self, key, default):
        self.key = key
        self.default = default

    def visit_Str(self, node):
        return ast.copy_location(
            ast.Name(id=self.key),
            node
        )


class AssignInspector(ast.NodeVisitor):
    """ Inspect assignemt to variable `var_name` and figure
        out if the RHS is a dictionary with "default" key,
        the value of which is another dictionary with a key
        specified in `find`, and replace that value with variable
        name specified in `env_replace` using `default` for default
        value if there's no env. variable with the specified name

    """
    def __init__(self, var_name, find, env_replace, default):
        self.find = find
        self.env_replace = env_replace
        self.default = default
        self.var_name = var_name

    def visit_Assign(self, node):
        children = list(ast.iter_child_nodes(node))
        if isinstance(children[1], ast.Dict) and children[0].id == self.var_name:
            dict_ = children[1]
            idx = find_key(dict_.keys, 'default')
            if idx is None:
                return
            dict_ = dict_.values[idx]
            idx = find_key(dict_.keys, self.find)
            transformer = ValueEnvTransformer(self.env_replace, self.default)
            dict_.values[idx] = transformer.visit(dict_.values[idx])


def process_settings_file(file_path):
	tree = ast.parse(open(file_path, 'r').read())
	visitors = [
	    # Transform configuration keys in DATABASES
	    AssignInspector('DATABASES', 'HOST', 'OPENSHIFT_PGSQL_HOST', ''),
	    AssignInspector('DATABASES', 'PORT', 'OPENSHIFT_PGSQL_PORT', ''),
	    # Transform configuration keys in CACHES
	    AssignInspector('CACHES', 'LOCATION', 'OPENSHIFT_MEMCACHED_HOST', '127.0.0.1:11211')
	]

	for visitor in visitors:
	    visitor.visit(tree)

	nodes = []
	if not check_os_imports(tree):
	    nodes.append(generate_import_os())
	nodes.append(generate_host_port_vars('PGSQL_SERVICE_SERVICE', 'tcp://127.0.0.1:5432', 'OPENSHIFT_PGSQL'))
	nodes.append(generate_host_var('MEMCACHED_SERVICE_SERVICE', 'tcp://127.0.0.1:11211', 'OPENSHIFT_MEMCACHED'))

	tree.body = nodes + tree.body

	return astor.to_source(tree)
