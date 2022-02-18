import functools
import logging
log = logging.getLogger("Dico_toolbox")

try:
    from soma import aims as _aims
    _HAS_AIMS = True
except ImportError:
    _HAS_AIMS = False
    log.warn("Can not import pyAims, are you in a brainvisa environment?")

def _with_brainvisa(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):      
        if not _HAS_AIMS:
            raise RuntimeError(
                "This function is only available in a brainvisa environment")
        return fun(*args, **kwargs)
    return wrapper