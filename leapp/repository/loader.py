import os
import pkgutil


def library_loader(mod, prefix, paths):
    to_add = []
    for importer, name, is_pkg in pkgutil.iter_modules(paths):
        imported = importer.find_module(name).load_module(name)
        to_add.append((prefix + '.' + name, imported))
        if mod:
            setattr(mod, name, imported)
        if is_pkg:
            to_add.extend(library_loader(imported, prefix + '.' + name, (os.path.join(importer.path, name),)))
    return to_add
