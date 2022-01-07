from . import _aims_tools
from . import transform
from . import data
from . import database
from . import wrappers
from . import convert
from . import graph
from . import skeleton
from . import bucket
from . import test_data
from . import mesh

import logging

log = logging.getLogger(__name__)

try:
    from soma import aims as _aims
    _HAS_AIMS = True
except ImportError:
    _HAS_AIMS = False
    log.warn("Can not import pyAims, are you in a brainvisa environment?")

from .info import __version__
