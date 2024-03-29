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

    return {"name": name, "mesh": mesh_dict}


def _parse_pool_result(res):
    name = res['name']
    mesh = PyMesh()
    mesh.from_elements(**res['mesh'])
    mesh = mesh.to_aims_mesh()

    return name, mesh


def _parse_pool_results(results):
    """Rebuild the multiprocessing results"""
    meshes = dict()
    for res in tqdm(results, desc="rebuilding results"):
        name, mesh = _parse_pool_result(res)
        meshes[name] = mesh
    return meshes


def mesh_of_point_clouds(pcs, pre_transformation=None, flip=False, post_transformation=None, **meshing_parameters):
    """Build the mesh of the pointclouds.

    Args:
        pcs (dict): the point clouds
        pre_transformation (collection of dict, optional): This transformation is applied before flip. keys = {dxy, rot, tra}. Defaults to None.
        flip (bool, optional): flip the data. Defaults to False.
        post_transformation (collection of dict, optional): This transformation is applied after flip. keys = {rot, tra}. Defaults to None.

    Returns:
        _type_: _description_
    """
    data = []
    for name, pc in pcs.items():
        data.append(dict(
            name=name,
            pc=pc,
            talairach=pre_transformation,  # {dxy, rot, tra}
            flip=flip,
            align=post_transformation,  # {rot, tra},
            meshing_parameters=meshing_parameters
        ))

    with Pool(cpu_count()-3) as pool:
        res = list(tqdm(pool.imap(mesh_one_point_cloud, data),
                   total=len(data), desc="meshing..."))

    # aims objects can not be pickled; the result parsing can not be parallelized with multiprocessing
        res = _parse_pool_results(res)

    return res


def shift_meshes_in_embedding(meshes:dict, embedding, scale=1):
    """Shift the meshes to an amount proportional to their position in the embedding.
    
    Args:
        -meshes:dict(name,ndarray) name:point-cloud dictionary
        -embedding:pandas.DataFrame the embedding of the point-clouds (e.g. isomap axis)
        -scale: multiplicative factor for the actual shift.
    
    Return:
        -name:dict(shifted_meshes)
    """
    shifted_meshes = dict()

    for name, mesh in tqdm(meshes.items(), desc="shifting"):
        shift_v = np.zeros(3)
        assert len(embedding.shape)<3, "For displaying, the embedding dimension must be < 3"

        if len(embedding.shape) == 1:
            shift_v[0] = embedding.loc[name]
        else:
            for i,v in enumerate(embedding.loc[name]):
                shift_v[i]=v


        shifted_mesh = shift_aims_mesh(mesh, shift_v, scale=scale)
        shifted_meshes[name] = shifted_mesh
    return shifted_meshes