import builtins
import importlib
import inspect

class ImportError(Exception):
    pass

def secure_importer(name, globals=None, locals=None, fromlist=(), level=0):
    frame = inspect.currentframe().f_back
    module_path = frame.f_globals['__file__']
    if module_path.endswith('/blueprint.py'):
        whitelist = ['blueprint','string','re','unicodedata','datetime','zoneinfo','calendar','collections','copy','numbers','math','cmath','decimal','fractions','random','statistics','secrets','csv','time','json','json.decoder','uuid','locale']
        frommodule = globals['__name__'] if globals else None
        if frommodule is None or frommodule == '__main__':
            if name not in whitelist:
                raise ImportError(f"Module '{name}' is restricted.")
        else:
            split = frommodule.split('.')
            if len(split) > 1:
                if split[0] not in whitelist:
                    raise ImportError(f"Module '{split[0]}' is restricted.")
            elif frommodule not in whitelist:
                raise ImportError(f"Module '{frommodule}' is restricted.")
    return importlib.__import__(name, globals, locals, fromlist, level)
builtins.__import__ = secure_importer
