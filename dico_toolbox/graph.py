from .wrappers import pyGraph as _pyGraph
from . import convert as _convert
import numpy as _np
from soma import aims as _aims

def get_vertices_by_name(name, graph):
    """Return all vertices with given name in the graph"""
    # with pyGraph
    # pyg = pyGraph(graph)
    # out = list(filter(lambda v : v.name == name, pyg.vertices))
    
    # without PyGraph
    out = list(filter(lambda v : v.get('name') == name, graph.vertices().list()))
    return out

buckets_labels = ['aims_ss', 'aims_other', 'aims_bottom']


def get_vertices_names(graph):
    pyg = _pyGraph(graph)
    return [v.name for v in pyg.vertices]


def stack_buckets(vertex, labels=["aims_ss", "aims_bottom", "aims_other"]):
    """Get and stack all the specified buckets in a graph's vertex"""
    vertex_bcks = list()
    for label in labels:
        bck = vertex.get(label)
        if bck is not None:
            bck_np = _convert.bucketMAP_aims_to_ndarray(bck)
            if len(bck_np) > 0:
                vertex_bcks.append(bck_np)
    try:
        stack = _np.vstack(vertex_bcks)
    except:
        stack = None
        print(vertex_bcks)
    
    return stack


def get_bucket_from_graph_by_suclus_name(graph, sulcus_name, ICBM2009c, labels=["aims_ss", "aims_bottom", "aims_other"]):
    """
    Get and stack all buckets in the graph corresponding to sulcus name and labels.
    
    if ICBM2009c is True, the buckets are transformed into the ICBM2009c Template coordinates.
    """
    graph_buckets = list()
    tr_aims = _aims.GraphManip.getICBM2009cTemplateTransform(graph)

    vertices = filter(lambda v : v.get("name") == sulcus_name and v.get('point_number') > 0, graph.vertices().list())
    
    for vertex in vertices:
        bck = stack_buckets(vertex, labels=labels)
        if ICBM2009c:
            bck_tr = tr_aims.transformPoints(bck)
        else:
            bck_tr = bck
        graph_buckets.append(bck_tr)
    
    return _np.vstack(graph_buckets)