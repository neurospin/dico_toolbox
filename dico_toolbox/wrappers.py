from soma import aims as _aims
import numpy as _np

class PyMesh:
    def __init__(self, aims_mesh=None):
        """A multi-frame mesh.

        Args:
            aims_mesh ([aims mesh], optional): if an aims mesh is passed to the class constructor,
            the mesh data is copied into the new object. Defaults to None.

        Raises:
            ValueError: when the aims_mesh is not conform.
        """
        self.frames = [PyMeshFrame()]
        self.header = {}
        if aims_mesh is not None:
            self.header = aims_mesh.header()
            self.frames = [None]*aims_mesh.size()
            for i in range(aims_mesh.size()):
                l = PyMeshFrame()
                try:
                    l.vertices = PyMesh._mesh_prop_to_numpy(
                        aims_mesh.vertex(i))
                    l.polygons = PyMesh._mesh_prop_to_numpy(
                        aims_mesh.polygon(i))
                    l.normals = PyMesh._mesh_prop_to_numpy(aims_mesh.normal(i))
                except:
                    raise ValueError("Invalid aims mesh")
                self.frames[i] = l

    @ property
    def vertices(self):
        return self.frames[0].vertices

    @ vertices.setter
    def vertices(self, v):
        self.frames[0].vertices = v

    @ property
    def polygons(self):
        return self.frames[0].polygons

    @ polygons.setter
    def polygons(self, v):
        self.frames[0].polygons = v

    @ property
    def normals(self):
        return self.frames[0].normals

    @ normals.setter
    def normals(self, v):
        self.frames[0].normals = v

    def append(self, frame):
        self.frames.append(frame)

    def __getitem__(self, i):
        try:
            return self.frames[i]
        except IndexError:
            raise IndexError("this mesh is empty")

    def __setitem__(self, i, v):
        self.frames[i] = v

    def __len__(self):
        return len(self.frames)

    def __repr__(self):
        return "Mesh of {} frame(s)\n{}".format(
            len(self.frames),
            '\n'.join([str(k)+': '+str(v) for k, v in self.header.items()])
        )

    def to_aims_mesh(self, header={}):
        """Get the aims mesh version of this mesh."""

        mesh = _aims.AimsTimeSurface()

        for i, frame in enumerate(self.frames):
            vertices = frame.vertices.tolist()
            polygons = frame.polygons.tolist()
            mesh.vertex(i).assign(vertices)
            mesh.polygon(i).assign(polygons)

        # update normals
        mesh.updateNormals()
        # update header
        mesh.header().update(header)

        return mesh

    @ staticmethod
    def _mesh_prop_to_numpy(mesh_prop):
        """return a new numpy array converting AIMS mesh properties
        into numpy ndarrays (soma.aims.vector_POINT2DF)"""
        return _np.array([x[:] for x in mesh_prop])


class PyMeshFrame:
    def __init__(self, frame=None):
        """One frame of a mesh with numpy array vertices, polygons and normals."""
        self.vertices = None
        self.polygons = None
        self.normals = None
        self.header = None

        if frame is not None:
            self.vertices = frame.vertices.copy()
            self.polygons = frame.polygons.copy()
            self.normals = frame.normals.copy()
            self.header = frame.header

    def __repr__(self):
        if self.polygons is not None:
            ln = len(self.polygons)
        else:
            ln = 0
        return "PyMeshFrame of {} triangles\n".format(ln)


class AimsObjAttribute:
    def __init__(self):
        pass

class pyVertex:
    def __init__(self, aimsVertex):
        self.aims_obj = aimsVertex
        aa = AimsObjAttribute()
        
        for k in self.aims_obj.keys():
            self.__dict__[k] = aa
            
    def to_aims(self):
        return self.aims_obj
            
    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        
        if isinstance(val, AimsObjAttribute):
            val = self.aims_obj.get(name)
            
        return val
        
    def __repr__(self):
        return f"{self.name}"
    
    
class pyGraph:
    def __init__(self, aimsGraph):
        assert( isinstance(aimsGraph, _aims.Graph))
        self.aims_obj = aimsGraph
        for k,v in self.aims_obj.items():
            self.__dict__[k]=v
        self.vertices = [pyVertex(v) for v in aimsGraph.vertices().list()]
        self.aimsvertices = aimsGraph.vertices().list()
        
    def to_aims(self):
        return self.aims_obj
    
    def __getattr__(self, name):
        return eval(f"self.aims_obj.{name}")
    
    def __repr__(self):
        return f"pyGraph of {len(self.vertices)} vertices"
    
    
def get_vertices_by_name(name, graph):
    """Return all vertices with given name in the graph"""
    # with pyGraph
    # pyg = pyGraph(graph)
    # out = list(filter(lambda v : v.name == name, pyg.vertices))
    
    # without PyGraph
    out = list(filter(lambda v : v.get('name') == name, graph.vertices().list()))
    return out

buckets_labels = ['aims_ss', 'aims_other', 'aims_bottom']
    