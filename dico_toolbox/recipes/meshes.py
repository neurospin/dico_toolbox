from multiprocessing import Pool, cpu_count
from .. mesh import shift_aims_mesh, transform_mesh_inplace, apply_Talairach_to_mesh, flip_mesh, transform_mesh
from ..convert import volume_to_mesh, bucket_to_mesh
from ..wrappers import PyMesh
import numpy as np
from tqdm import tqdm


class Average_result:
    """Store the result of averaging a set of point-clouds"""

    def __init__(self, vol, offset, n, rotation=None, translation=None, coord_in_embedding=None):
        self.n = n
        self.vol = vol
        self.offset = offset
        self.translation = translation
        self.rotation = rotation
        self.coord_in_embedding = coord_in_embedding

    def __repr__(self):
        return f"Average of {self.n} point-clouds"


def mesh_of_average(average_result, in_embedding=False, embedding_scale=1, **meshing_parameters):
    """Generate the meshe of the given average-result.

    Args:
        average_result (Average_result): the result of averaging a point-cloud cluster
        in_embedding (bool, optional): translate the mesh to the position of the central point-cloud in the embedding. Defaults to False.
        embedding_scale (int, optional): scale factor for the embedding coordinates.
        It can be used to improve the visualization of the moving averages by increasing their distance. Defaults to 1.

        meshing_parameters are passed to the function `dico_toolbox.volume_to_mesh()`

    Returns:
        aims_mesh : the drawable mesh of the point-cloud
    """
    # make mesh
    mesh = volume_to_mesh(average_result.vol, **meshing_parameters)
    # translate the mesh into the original bucket coordinate system
    mesh = shift_aims_mesh(mesh, average_result.offset)
    if in_embedding and len(average_result.coord_in_embedding) <= 2:
        v = np.zeros(3)
        for i, x in enumerate(average_result.coord_in_embedding):
            v[i] = x
        transform_mesh_inplace(mesh, np.eye(3), v*embedding_scale)
    return mesh


def mesh_of_averages(average_results, in_embedding=False, embedding_scale=1, **meshing_parameters):
    """Generate meshes of the given average-results.
    Agerage results are tipically generated by the pcpm (point-cloud-pattern-mining) module.

    Args:
        average_results (dict): {label:average_result}
        in_embedding (bool, optional): translate the mesh to the position of the central point-cloud in the embedding. Defaults to False.
        embedding_scale (int, optional): scale factor for the embedding coordinates.
        It can be used to improve the visualization of the moving averages by increasing their distance. Defaults to 1.

    Returns:
        dict: {label:aims_mesh}
    """
    return {k: mesh_of_average(v, in_embedding, embedding_scale, **meshing_parameters) for k, v in average_results.items()}


def mesh_one_point_cloud(data):
    """build one mesh. This function is adapted for multiprocessing"""
    # unpack data
    name = data['name']
    pc = data['pc']
    tal = data["talairach"]
    flip = data['flip']
    align = data["align"]
    shift = data["shift"]
    meshing_parameters = data['meshing_parameters']

    # generate mesh
    mesh = bucket_to_mesh(pc, **meshing_parameters)
    # Talairach transform
    if tal is not None:
        mesh = apply_Talairach_to_mesh(
            tal['dxyz'], tal['rot'], tal['tra'], flip=False)
    if flip:
        mesh = flip_mesh(mesh)
    # apply alignment
    if align is not None:
        mesh = transform_mesh(
            mesh, rot_matrix=align['rot'],  transl_vec=align['tra'])
    # convert to dictionnary
    mesh_dict = PyMesh(mesh).to_dict()

    # shift mesh
    mesh_shifted = None
    mesh_shifted_dict = None
    if shift is not None and len(shift) <= 3:
        # The user gave an offset and the embedding dimension is <=3
        assert len(shift) <= 3, "embedding dimension must be <= 3"
        v = np.zeros(3)
        for i, x in enumerate(shift):
            v[i] = x
        mesh_shifted = transform_mesh(
            mesh, rot_matrix=np.eye(3), transl_vec=v)
        mesh_shifted_dict = PyMesh(mesh_shifted).to_dict()

    return {"name": name, "mesh": mesh_dict, "shifted_mesh": mesh_shifted_dict}


def _parse_pool_result(res):
    name = res['name']
    mesh = PyMesh()
    mesh.from_elements(**res['mesh'])
    mesh = mesh.to_aims_mesh()
    # rebuild
    shifted_mesh = None
    if res['shifted_mesh'] is not None:
        shifted_mesh = PyMesh()
        shifted_mesh.from_elements(**res['shifted_mesh'])
        shifted_mesh = shifted_mesh.to_aims_mesh() if shifted_mesh is not None else None

    return name, mesh, shifted_mesh


def _parse_pool_results(results):
    """Rebuild the multiprocessing results"""
    meshes = dict()
    shifted_meshes = dict()
    for res in tqdm(results, desc="rebuilding results"):
        # rebuild
        name, mesh, shifted_mesh = _parse_pool_result(res)
        meshes[name] = mesh
        shifted_meshes[name] = shifted_mesh

    return meshes, shifted_meshes


def mesh_of_point_clouds(pcs, pre_transformation=None, flip=False, post_transformation=None, embedding=None, embedding_scale=1, **meshing_parameters):
    data = []
    for name, pc in pcs.items():
        shift = None
        if embedding is not None:
            shift = embedding.loc[name].values*embedding_scale
        data.append(dict(
            name=name,
            pc=pc,
            talairach=pre_transformation,  # {dxy, rot, tra}
            flip=flip,
            align=post_transformation,  # {rot, tra},
            shift=shift,  # [x,y,z]
            meshing_parameters=meshing_parameters
        ))

    with Pool(cpu_count()-3) as pool:
        res = list(tqdm(pool.imap(mesh_one_point_cloud, data),
                   total=len(data), desc="meshing..."))

    # aims objects can not be pickled; the result parsing can not be parallelized with multiprocessing
        res = _parse_pool_results(res)

    return res
