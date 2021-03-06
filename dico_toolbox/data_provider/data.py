from glob import glob
import os
import re
from difflib import get_close_matches
from .._tools import _with_brainvisa

class paths:
    dico = "/neurospin/dico"

class pclean:
    """file provider for the plcean folder"""

    base = "/neurospin/dico/data/bv_databases/human/pclean/all"
    subfolders = glob(f"{base}/*/")
    arg_path_suffix = "t1mri/t1/default_analysis/folds/3.3/base2018_manual/"
    skeleton_path_suffix = "t1mri/t1/default_analysis/segmentation/"

    # the absolute paths of the arg files
    # eg /neurospin/lnao/PClean/database_learnclean/all/sujet01/t1mri/t1/default_analysis/folds/3.3/base2018_manual/Rsujet01_base2018_manual.arg
    graph_paths = list()
    for subfolder in subfolders:
        graph_paths += glob(f"{subfolder}{arg_path_suffix}*.arg")

    # file names of all args (withour lmeading L or R)
    names = list(
        set(map(lambda s: os.path.basename(s).split('.')[0][1:], graph_paths)))

    @classmethod
    def get_graph_path_by_name(cls, name, side):
        """Get the absolute path of an arg file by file basename and side(L or R)"""
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
        """Get the aims graph by file basename and side(L or R)"""
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
