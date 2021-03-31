import builtins
import traceback
import importlib
import inspect
import sys

def import2(name, globals=None, locals=None, fromlist=(), level=0):
    f1 = None
    f2 = None
    try:
        f1 = sys._getframe(0).f_globals['__name__'] # compiled
    except Exception:
        pass
    try:
        f2 = sys._getframe(1).f_globals['__name__'] # non-compiled
    except Exception:
        pass

    if (f1 is not None and f1 == 'blueprint') or (f2 is not None and f2 == 'blueprint'):
        whitelist = ['blueprint','traceback','string','re','unicodedata','datetime','zoneinfo','calendar','collections','copy','numbers','math','cmath','decimal','fractions','random','statistics','fnmatch','secrets','csv','time','json','json.decoder','uuid','locale']
        frommodule = globals['__name__'] if globals else None
        if frommodule is None or frommodule in ['__main__','blueprint']:
            if name not in whitelist:
                raise Exception(f"Module '{name}' is restricted.")
        else:
            split = frommodule.split('.')
            if len(split) > 1:
                if split[0] not in whitelist:
                    raise Exception(f"Module '{split[0]}' is restricted.")
            elif frommodule not in whitelist:
                raise Exception(f"Module '{frommodule}' is restricted.")
    return importlib.__import__(name, globals, locals, fromlist, level)

def exec2(name, globals=None, locals=None):
    frame = inspect.currentframe().f_back
    if frame is not None:
        module_path = frame.f_globals['__file__']
        if module_path.endswith('/blueprint.py'):
            raise Exception("Method exec() is restricted.")
    origin_exec(name, globals, locals)

def open2(path, *args, **kwargs):
    frame = inspect.currentframe().f_back
    if frame is not None and frame.f_globals['__file__'].endswith('/blueprint.py'):
        a = inspect.currentframe().f_globals['__file__']
        b = inspect.currentframe().f_back.f_globals['__file__']
        c = inspect.currentframe().f_back.f_back.f_globals['__file__']
        d = inspect.currentframe().f_back.f_back.f_back.f_globals['__file__']
        raise Exception("Method open() is restricted. " + a + ' | ' + b + ' | ' + c + ' | ' + d)
    return origin_open(path, *args, **kwargs)

origin_exec = builtins.exec
origin_open = builtins.open
builtins.exec = exec2
builtins.__import__ = import2
builtins.open = open2
