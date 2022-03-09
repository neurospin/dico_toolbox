# [treesource] pyAims Graph manipulation
from logging import warning
import os.path as _op
from . import convert as _convert
import numpy as _np
from soma import aims as _aims
from ._dev import _deprecation_alert_decorator


BUCKETS_TYPES = ['aims_ss', 'aims_other', 'aims_bottom']
SPACES_TRANSFORMERS = {
    None: lambda graph: None,
    "ICBM2009c": _aims.GraphManip.getICBM2009cTemplateTransform,
    "Talairach": _aims.GraphManip.talairach
}


def _check_graph(graph):
    """ Check that graph is actually a graph and load it if it is a path. """
    if isinstance(graph, str):
        graph = _aims.read(graph)
    if not isinstance(graph, _aims.Graph):
        raise ValueError(
            "soma.aims.Graph was expected. {} given.".format(type(graph)))
    return graph


def get_vertices_by_key(graph, key, needed_values):
    """Return all vertices with given key in the graph"""
    if not isinstance(needed_values, (list, tuple)):
        needed = [needed_values]
    out = list(filter(lambda v: v.get(key) in needed_values,
               _check_graph(graph).vertices().list()))
    return out


@_deprecation_alert_decorator(use_instead=get_vertices_by_key)
def get_vertices_by_name(name, graph):
    """Return all vertices with given name in the graph"""
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
    values_gen = _get_property_from_list_of_dict(
        _check_graph(graph).vertices().list(), prop, filt)
    return list(values_gen)


def get_property_from_edges(graph, prop, filt=None):
    """Get the property from all edges in graph.
    Filt is a boolean function used to filter the edges.

    If the property does not exist or is None, it is not returned.
    """
    values_gen = _get_property_from_list_of_dict(
        _check_graph(graph).edges().list(), prop, filt)
    return list(values_gen)


def stack_vertex_buckets(vertex, bck_types=BUCKETS_TYPES):
    """Get and stack all the specified buckets in a graph's vertex

        Coordinates are expressed in millimeters
    """
    vertex_bcks = list()
    for bck_type in bck_types:
        bck = vertex.get(bck_type)
        if bck is not None:
            bck_np = _convert.bucketMAP_aims_to_ndarray(bck)
            if len(bck_np) > 0:
                vertex_bcks.append(bck_np)
    try:
        stack = _np.vstack(vertex_bcks)
    except:
        stack = None

    return stack


def list_buckets(graph, key=None, needed_values=None, return_keys=None, defaults=None, transform=None, bck_types=BUCKETS_TYPES):
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

    graph = _check_graph(graph)

    # Select vertices
    if key is None:
        vertices = graph.vertices()
    else:
        if needed_values is None:
            vertices = filter(lambda v: v.get(key) and v.get(
                'point_number') > 0, graph.vertices().list())
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
        bck = stack_vertex_buckets(vertex, bck_types=bck_types)
        if bck is None:
            continue
        bck_tr = tr_aims.transformPoints(bck) if tr_aims else bck
        if len(bck_tr.shape) < 2:
            bck_tr = [bck_tr]
        graph_buckets.append(bck_tr)
        for k in key_values:
            val = vertex.get(k)
            key_values[k].append(defaults[k] if val is None else val)

    # Return a flat vector of bucket points
    if return_keys is not None:
        return graph_buckets, key_values[return_keys[0]] if return_as_list else key_values
    else:
        return graph_buckets, {}


def stack_buckets(graph, key=None, needed_values=None, return_keys=None, defaults=None, transform=None, bck_types=BUCKETS_TYPES):
    """ Stack bucket listed by list_buckets() """
    graph_buckets, key_values = list_buckets(
        graph, key, needed_values, return_keys, defaults, transform, bck_types)
    if len(return_keys):
        return _np.vstack(graph_buckets), key_values
    return _np.vstack(graph_buckets)


@_deprecation_alert_decorator(use_instead=stack_buckets)
def get_bucket_from_graph_by_suclus_name(graph, sulcus_name, ICBM2009c,
                                         bck_types=BUCKETS_TYPES):
    """
    Get and stack all buckets in the graph corresponding to sulcus name and bucket types.

    if ICBM2009c is True, the buckets are transformed into the ICBM2009c Template coordinates.
    """
    return stack_buckets(graph, 'name', sulcus_name, "ICBM2009c" if ICBM2009c else None, bck_types)
