# [treesource] pyAims Graph manipulation
from logging import warning
import os.path as _op
from typing import Iterable
from . import convert as _convert
import numpy as _np
from soma import aims as _aims
import sigraph
from ._dev import _deprecation_alert_decorator
import pandas as pd
import numpy as np


BUCKETS_TYPES = ['aims_ss', 'aims_other', 'aims_bottom']
SPACES_TRANSFORMERS = {
    None: lambda graph: None,
    "ICBM2009c": _aims.GraphManip.getICBM2009cTemplateTransform,
    "Talairach": _aims.GraphManip.talairach
}


VERTEX_KEYNAMES = [
    'bottom_point_number',    # 7
    'name',                   # S.O.T.lat.med._left
    'point_number',           # 20
    'size',                   # 26.3672
    'skeleton_label',         # 3380
    'ss_point_number',        # 12
    'CSF_volume',             # 156.885
    'GM_volume',              # 449.561
    'LCR_volume',             # 156.885
    # 'Tal_boundingbox_max',    # 49.0176 54.7348 24.7251
    # 'Tal_boundingbox_min',    # 45.88 49.7386 19.7009
    'Tmtktri_label',          # 309
    'bottom_label',           # 309
    # 'boundingbox_max',        # 177 171 83
    # 'boundingbox_min',        # 174 166 80
    # 'depth_direction',        # 0 0.460645 -0.887584
    # 'depth_direction_weight', # 12.2801
    # 'direction',              # 0.544827 -0.744282 -0.386273
    # 'gravity_center',         # 175.2 168.25 81.45
    # 'grey_surface_area',      # 112.913
    # 'hull_normal',            # 0.0778637 0.42825 -0.900299
    'hull_normal_weight',     # 13.6991
    'index',                  # 309
    'maxdepth',               # 8.26
    'mean_depth',             # 6.47429
    'mid_interface_voxels',   # 82
    'mindepth',               # 0
    # 'moments',                # 26.3672 4330.81 4159.01 3221.41 26.8822 50.6937 74.0094 -33.6027 -3.3371 -0.463486 8.60345 2.0368 15.5509 -11.2975 -0.139046 10.3198 -7.16954 -0.500565 -13.9741 1.91188
    # 'normal',                 # 0.816492 0.575818 0.0421368
    'other_label',            # 309
    'other_point_number',     # 1
    # 'refdepth_direction',     # -0.0516759 0.280079 -0.958585
    # 'refdirection',           # 0.529934 -0.805888 -0.264034
    # 'refgravity_center',      # 47.1613 52.2559 21.6773
    # 'refhull_normal',         # 0.0329655 0.239068 -0.970443
    'refmaxdepth',            # 9.26
    'refmean_depth',          # 7.24571
    'refmindepth',            # 0
    # 'refnormal',              # 0.81883 0.567257 -0.0879543
    'refsize',                # 32.5143
    'refsurface_area',        # 110.751
    'rootsbassin',            # 366
    'ss_label',               # 309
    'surface_area',           # 94.8557
    # 'talcovar',               # 44505.2 49262.7 20452.5 49262.7 54654.4 22657.5 20452.5 22657.5 9470.56
    'thickness_mean',         # 5.13603
    'thickness_std',          # 1.24796
    'white_surface_area',     # 91.1045
    'label'
]


def _check_graph(graph, translation_file=None):
    """ Check that graph is actually a graph and load it if it is a path. """
    if isinstance(graph, str):
        graph = _aims.read(graph)
    if not isinstance(graph, _aims.Graph):
        raise ValueError(
            "soma.aims.Graph was expected. {} given.".format(type(graph)))
    if translation_file is not None:
        flt = sigraph.FoldLabelsTranslator()
        flt.readLabels(translation_file)
        flt.translate(graph)
    return graph


def check_graph(graphs, translation_file=None) -> _aims.Graph or List[_aims.Graph]:
    """ Check that graph is actually a graph and load it if it is a path. 

        Parameters
        ----------
        graphs: str or list of str or Aims FGraph or list of Aims FGraph
            One or several graph object or file path to check.
        translation_file: str, optional

        Return
        ------
        A single graph if graphs is not a list or tuple. A list of graphs otherwise.
    """
    if isinstance(graphs, (tuple, list)):
        return list(_check_graph(graph, translation_file) for graph in graphs)
        # FIXME: _aims.Graph are not pickable, need to use pyGraph
        # njobs: int (opt.)
        #     Number of parallel jobs to use to check all the graphs.
        #     If < 1 it use all the CPUs minus njobs.
        #     Default is 1.
        # njobs = cpu_count() - njobs if njobs < 1 else min(njobs, cpu_count())
        # return Parallel(n_jobs=max(njobs, 1))(delayed(_check_graph)(g) for g in graphs)
    else:
        return _check_graph(graphs)


def get_vertices_by_key(graph, key, needed_values):
    """Return all vertices with given key in the graph"""
    graph = _check_graph(graph)
    if not isinstance(needed_values, (list, tuple)):
        needed_values = [needed_values]
    out = list(filter(lambda v: v.get(key) in needed_values,
               _check_graph(graph).vertices().list()))
    return out


@_deprecation_alert_decorator(use_instead=get_vertices_by_key)
def get_vertices_by_name(name, graph):
    """Return all vertices with given name in the graph"""
    graph = _check_graph(graph)
    return get_vertices_by_key(graph, 'name', name)


def _get_property_from_list_of_dict(lst, prop, filt=None):
    """Get property from a list of dictionnary.
    Return a generator.

    If the property does not exist or is None, it is not returned.
    """
    # Use no filter if none is specified
    def filt(x): return True if filt is None else filt
    values_gen = (x.get(prop, None) for x in lst if filt(x))
    values_gen = filter(lambda x: x is not None, values_gen)
    return values_gen


def get_property_from_vertices(graph, prop, filt=None):
    """Get the property from all vertices in graph.
    Filt is a boolean function used to filter the vertices.

    If the property does not exist or is None, it is not returned.
    """
    graph = _check_graph(graph)
    values_gen = _get_property_from_list_of_dict(
        _check_graph(graph).vertices().list(), prop, filt)
    return list(values_gen)


def get_property_from_edges(graph, prop, filt=None):
    """Get the property from all edges in graph.
    Filt is a boolean function used to filter the edges.

    If the property does not exist or is None, it is not returned.
    """
    graph = _check_graph(graph)
    values_gen = _get_property_from_list_of_dict(
        _check_graph(graph).edges().list(), prop, filt)
    return list(values_gen)


def stack_vertex_buckets(vertex, bck_types=BUCKETS_TYPES, scale=True):
    """Get and stack all the specified buckets in a graph's vertex

        Coordinates are expressed in millimeters
    """
    vertex_bcks = list()
    for bck_type in bck_types:
        bck = vertex.get(bck_type)
        if bck is not None:
            bck_np = _convert.bucketMAP_aims_to_ndarray(bck, scale)
            if len(bck_np) > 0:
                vertex_bcks.append(bck_np)
    try:
        stack = _np.vstack(vertex_bcks)
    except:
        stack = None

    return stack


def list_buckets(graph, key=None, needed_values=None, return_keys=None, defaults=None, transform=None, bck_types=BUCKETS_TYPES, scale=True):
    """ List all buckets of the graph that correspond to needed key values and bucket types.
        Also return values of each vertex for the specified keys.

        Parameters
        ==========
        graph: soma.aims.Graph | str
            AIMS Cortical Graph

        key: str (opt.)
            Select vertices that have key property.

        needed_values: list | single value (opt.)
            Select vertices that have key value equal to one of the needed values.

        return_keys: list | str | None (opt.)
            Additionally, this function can extract other properties from each graph vertex.
            The properties to extract can be indicated in this parameter as a string or a list of str.
            If a string is given, the function returns a list containing the property values.
            If a list of string is used, the return is a dictionnary of values corresponding to each given key.

        defaults: list | str | None (opt.)
            When return_keys is not None, if a key is not defined in a vertex,
            defaults are used to set up the value. If defaults is a single value,
            the value is used for all the keys. Default is None.

        transform: "ICBM2009c" | "Talairach" | None (opt.)
            Apply known transformation defined in the SPACES_TRANSFORMERS dictionnary.
            Two spaces are available: "Talairach" and "ICBM2009c"(refers to the MNI space used by BrainVISA).
            None value skip the transformation step.
            Default is None.

        bck_types: list of str (opt.)
            Bucket keys used to list points.
            Default is ['aims_ss', 'aims_other', 'aims_bottom']., which are the specified in BUCKETS_TYPES.

        scale: boolean (opt., default: True)
            If True, the coordinates are multiplied by the voxel size, else the coordinates are in digital space (voxels).
            Note that is a trnasform is performed, it should be set to True otherwise an erro is raised.

        Return
        ======
        Return a Tuple (buckets, other_values). If return_keys is none, other_values is an empty dictionnary.


        Examples
        ========
        Return buckets of all vertex
        '''python
        stack_buckets(graph, 'name', return_keys='name', default='unknown', transform="Talairach")
        '''

        Return buckets, name and vertex index of automatically labeled as 'S.T.S.asc' in the image space. 
        Name and vertex index is set to None if not defined.
        '''python
        stack_buckets(graph, 'label', needed=['S.T.S.asc'], return_keys=['name', 'vertex_index'], default=None)
        '''

        Return buckets and names of all vertex (with name set to 'unknown' if undefined)
        '''python
        stack_buckets(graph, 'name', return_keys='name', default='unknown', transform="Talairach")
        '''

    """
    if isinstance(graph, dict):
        # It is actually a vertex (because of previous implementation)
        raise ValueError(
            "stack_buckets() is now used for graph. Use stack_vertex_buckets instead()")
    if not transform in SPACES_TRANSFORMERS.keys():
        raise ValueError('"transform" parameter should one of: {}. {} given'.format(list( SPACES_TRANSFORMERS.keys()), transform))

    if transform and not scale:
        raise ValueError("No transformation can be applied to vertex coordinates if the value are not scaled with the graph voxel size. Set scale to True or transform to None.")
    
    graph = _check_graph(graph)

    # Select vertices
    if key is None:
        vertices = graph.vertices()
    else:
        if needed_values is None:
            # FIXEME: Error with point_number ???
            # vertices = filter(lambda v: v.get(key) and  v.get(
            #     'point_number') and v.get(
            #     'point_number') > 0, graph.vertices().list())
            vertices = filter(lambda v: v.get(key), graph.vertices().list())
        else:
            if not isinstance(needed_values, list):
                needed_values = [needed_values]
            vertices = filter(lambda v: v.get(key) in needed_values and v.get(
                'point_number') > 0, graph.vertices().list())

    # Initialize return dictionnary and extend default values if needed
    return_as_list = False
    if return_keys:
        if not isinstance(return_keys, (list, tuple)):
            return_as_list = True
            return_keys = [return_keys]
        if not isinstance(defaults, (list, tuple)):
            defaults = [defaults] * len(return_keys)
        key_values = {k: [] for k in return_keys}
    else:
        key_values = {}

    # Concatenate buckets of all selected vertices, list needed values
    # and transform them if needed
    tr_aims = SPACES_TRANSFORMERS[transform](graph)
    graph_buckets = list()
    for vertex in vertices:
        bck = stack_vertex_buckets(vertex, bck_types=bck_types, scale=scale)
        if bck is None:
            continue
        bck_tr = tr_aims.transformPoints(bck) if tr_aims else bck
        if len(bck_tr.shape) < 2:
            bck_tr = [bck_tr]
        graph_buckets.append(bck_tr)
        for ik, k in enumerate(key_values):
            val = vertex.get(k)
            key_values[k].append(defaults[ik] if val is None else val)

    # Return a flat vector of bucket points
    if return_keys is not None:
        return graph_buckets, key_values[return_keys[0]] if return_as_list else key_values
    else:
        return graph_buckets, {}


def stack_buckets(graph, key=None, needed_values=None, return_keys=None, defaults=None, transform=None, bck_types=BUCKETS_TYPES, scale=True):
    """ Stack bucket listed by list_buckets() """
    graph = _check_graph(graph)
    graph_buckets, key_values = list_buckets(
        graph, key, needed_values, return_keys, defaults, transform, bck_types, scale)
    if len(return_keys):
        values = {}
        for k in key_values:
            values[k] = []
            for v, val in enumerate(key_values[k]):
                values[k].extend([val] * len(graph_buckets[v]))
        return _np.vstack(graph_buckets), values
    return _np.vstack(graph_buckets), {}


@_deprecation_alert_decorator(use_instead=stack_buckets)
def get_bucket_from_graph_by_suclus_name(graph, sulcus_name, ICBM2009c,
                                         bck_types=BUCKETS_TYPES):
    """
    Get and stack all buckets in the graph corresponding to sulcus name and bucket types.

    if ICBM2009c is True, the buckets are transformed into the ICBM2009c Template coordinates.
    """
    return stack_buckets(graph, 'name', sulcus_name, "ICBM2009c" if ICBM2009c else None, bck_types)

                
def sulci_names(graph, translation_file=None):
    """ Return the list of sulci names found in the graph."""
    graph = check_graph(graph)
    if translation_file is not None:
        flt = sigraph.FoldLabelsTranslator()
        flt.readLabels(translation_file)
        flt.translate(graph)
    
    return list(set(get_property_from_vertices(graph, 'name') + get_property_from_vertices(graph, 'label')))


def stack_as_dict(graph, key=None, needed_values=None, columns=VERTEX_KEYNAMES, defaults=None, voxel_size=None, transform=None, bck_types=BUCKETS_TYPES) -> dict:
    """ Return graĥ data in a dictionnary.
    
    Each key correspond to a vertex property. All the keys return a list with the same length (number of points)
    The dictionnary contain at least: 
        * 'u', 'v', 'w': The coordinate of each surviving point in digital space (unit: voxels)
        * 'x', 'y', 'z': The coordinate of each surviving point in real world space after transformation(unit: same as vowel_size, generally millimeters)
    """
    graph = _check_graph(graph)
    # Points: voxel coordinates (digital space)
    points, other_data = stack_buckets(graph, key, needed_values, return_keys=columns, defaults=defaults, transform=None, bck_types=bck_types, scale=False)
    n_points = len(points)

    if voxel_size:
        if not isinstance(voxel_size, (Iterable)):
            voxel_size = [voxel_size, voxel_size, voxel_size]
        if len(voxel_size) != 3:
            raise ValueError('Invalid voxel size: {}'.format(voxel_size))
        gvs = graph['voxel_size']
        #rx, ry, rz = voxel_size[0] / gvs[0], voxel_size[1] / gvs[1], voxel_size[2] / gvs[2]
        rx, ry, rz = gvs[0] / voxel_size[0], gvs[1] / voxel_size[1], gvs[2] / voxel_size[2]

        # Filter voxel coordinates to subsample
        newcoords = np.round(points * [rx, ry, rz]).astype(int)
        subpoints, indices = np.unique(newcoords, axis=0, return_index=True)
        indices = list(sorted(indices))
    else:
        rx, ry, rz = 1., 1., 1.
        subpoints = points
        indices = np.arange(n_points)

    vs = graph['voxel_size']
    tr_aims = SPACES_TRANSFORMERS[transform](graph)
    data = {k: [0]*n_points for k in ['u', 'v', 'w', 'x', 'y', 'z']}
    # TODO: avoid for loop ! tr_aims take a 2d array as input so use it! =D
    for ip, p in enumerate(subpoints):
        # Scalling: The point in real world coordinate (millimeters)
        real_p = p * vs
        # Transform and resample
        x, y, z = tr_aims.transformPoints(np.atleast_2d(real_p))[0] if tr_aims else p
        data['u'][ip] = p[0]
        data['v'][ip] = p[1]
        data['w'][ip] = p[2]
        data['x'][ip] = x
        data['y'][ip] = y
        data['z'][ip] = z

    for k in other_data.keys():
        data[k] = []
        for idx in indices:
            data[k].append(other_data[k][idx])
    return data