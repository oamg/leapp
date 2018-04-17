import os
import pkgutil


def library_loader(mod, prefix, paths):
    """
    Prepares modules and packages to be loaded

    :param mod: module namespace
    :type mod: Python Module?
    :param prefix: prefix of module/package
    :type prefix: str
    :param paths: iterable paths
    :type paths: tuple(str) 
    :return: List of prepared modules/packages to be added (injected)
    """
    to_add = []
    for importer, name, is_pkg in pkgutil.iter_modules(paths):
        imported = importer.find_module(name).load_module(name)
        to_add.append((prefix + '.' + name, imported))
        if mod:
            setattr(mod, name, imported)
        if is_pkg:
            to_add.extend(library_loader(imported, prefix + '.' + name, (os.path.join(importer.path, name),)))
    return to_add
