from glob import glob
import os, re
import logging
from difflib import get_close_matches
import functools

log = logging.getLogger(__name__)

try:
    from soma import aims as _aims
    HAS_AIMS = True
except ImportError:
    HAS_AIMS = False
    log.warn("Can not import pyAims, are you in a brainvisa environment?")
    

def _with_brainvisa(fun):
    @functools.wraps(fun)
    def wrapper(*args,**kwargs):
        if not HAS_AIMS: raise RuntimeError("This function is only available in a brainvisa environment")
        return fun(*args,**kwargs)
    return wrapper


class paths:
    dico = "/neurospin/dico"

    
class learnclean:
    """file provider for the folder /neurospin/lnao/PClean/database_learnclean"""

    base = "/neurospin/lnao/PClean/database_learnclean/all"
    subfolders = glob(f"{base}/*/")
    arg_path_suffix = "t1mri/t1/default_analysis/folds/3.3/base2018_manual/"
    
    # the absolute paths of the arg files
    # eg /neurospin/lnao/PClean/database_learnclean/all/sujet01/t1mri/t1/default_analysis/folds/3.3/base2018_manual/Rsujet01_base2018_manual.arg
    graph_paths = list()
    for subfolder in subfolders:
        graph_paths += glob(f"{subfolder}{arg_path_suffix}*.arg")
    
    # the absolute paths of all left arg files
    left_paths = list(filter(lambda s: os.path.basename(s).startswith('L'), graph_paths))
    
    # the absolute paths of all right arg files
    right_paths = list(filter(lambda s: os.path.basename(s).startswith('L'), graph_paths))
    
    # file names of all args (withour lmeading L or R)
    names = list(set(map(lambda s : os.path.basename(s).split('.')[0][1:], graph_paths)))
    
    @classmethod
    def get_graph_path_by_name(cls, name, side):
        """Get the absolute path of an arg file by file basename and side (L or R)"""
        assert isinstance(name, str)
        assert side.upper() in "LR", "Side must be either 'L' or 'R'"

        if not name in learnclean.names:
            m = get_close_matches(name, cls.names)
            s = f" Did you mean '{m[0]}' ?" if m else ''
            raise ValueError(f"'{name}' is not a valid valid name.{s}")
                      
        r = re.compile(f".*?{side.upper()}({name}).arg")
        return list(filter(r.match, cls.graph_paths))[0] 

    @classmethod
    @_with_brainvisa
    def get_graph_by_name(cls, name, side):
        """Get the aims graph by file basename and side (L or R)"""
        path = cls.get_graph_path_by_name(name, side)
        graph = _aims.read(path)        
        return graph
    
    @classmethod
    @_with_brainvisa
    def get_left_graph_by_name(cls, name):
        """Get the LEFT aims graph by file basename"""
        return cls.get_graph_by_name(name, 'L')

    @classmethod
    @_with_brainvisa
    def get_right_graph_by_name(cls, name):
        """Get the RIGHT aims graph by file basename"""
        return cls.get_graph_by_name(name, 'R')