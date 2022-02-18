import functools
import logging

logger = logging.getLogger("dico_toolbox_dev")

def _deprecation_alert_decorator(use_instead):
    def real_decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            logger.warning(f"The function {function.__name__} is deprecated. Use {use_instead.__name__} instead.")
            return use_instead(*args, **kwargs)
        return wrapper
    return real_decorator