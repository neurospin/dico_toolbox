# [treesource] PyAims Mesh manipulation
from soma import aims as _aims
import numpy as _np
from . import transform as _transform


def rescale_mesh(mesh, dxyz):
    """Rescale a mesh by multiplying its vertices with the factors in dxyx.
    The rescaling is done in place."""
    for i in range(mesh.size()):
        mesh.vertex(i).assign(
            [_aims.Point3df(_np.array(x[:])*dxyz) for x in mesh.vertex(i)])


def copy_mesh(mesh):
    """Return a copy of the mesh"""
    return _aims.AimsTimeSurface(mesh)


def flip_mesh(mesh, axis=0):
    """Flip the mesh by inverting the specified axis.

    This function modifies the input mesh.

    Return None."""
    flip_v = _np.ones(3)
    flip_v[axis] = -1
    for i in range(mesh.size()):
        mesh.vertex(i).assign(
            [_aims.Point3df(_np.array(x[:])*flip_v) for x in mesh.vertex(i)])


def transform_mesh_inplace(mesh, rot_matrix=_np.eye(3), transl_vec=_np.zeros(3)):
    """Applay an affine tranformation to the mesh.
    The tranformation happens in-place, the input mesh is motified.

    Return None.
    """
    M = _transform.get_aims_affine_transform(rot_matrix, transl_vec)
    _aims.SurfaceManip.meshTransform(mesh, M)


def transform_mesh(mesh, rot_matrix=_np.eye(3), transl_vec=_np.zeros(3)):
    """Applay an affine tranformation to the mesh.
    The tranformation happens in-place, the input mesh is motified.

    Return a new transformed mesh.
    """
    M = _transform.get_aims_affine_transform(rot_matrix, transl_vec)
    tr_mesh = copy_mesh(mesh)
    _aims.SurfaceManip.meshTransform(tr_mesh, M)
    return tr_mesh


def shift_aims_mesh(mesh, offset, scale=1):
    """Translate each mesh with a specified offset.

    The offset must be an iterable of 3 elements (a 3D vector).

    The scale parameter multiplies the distance values before applying the translation.
    Returns a shifted mesh
    """
    try:
        iter(offset)
    except TypeError:
        raise TypeError(
            "Offset must be an iterable of length 3. Use shift_aims_mesh_along_axis() to apply a scalar offset to a given axis")

    if len(offset) != 3:
        raise ValueError("len(offset) must be 3.")

    offset_mesh = _aims.AimsTimeSurface(mesh)
    vertices = _np.array([x[:] for x in mesh.vertex(0)])
    for axis in range(3):
        vertices[:, axis] += offset[axis]*scale
    offset_mesh.vertex(0).assign(vertices.tolist())
    return offset_mesh


def shift_aims_mesh_along_axis(mesh, offset, scale=1, axis=1):
    """Translate a mesh."""
    shift_v = _np.zeros(3)
    shift_v[axis] = offset
    # return shift_aims_mesh(mesh, shift_v, scale=scale)
    return transform_mesh(mesh, transl_vec=shift_v*scale)


def join_meshes(meshes):
    """Join meshes.
    All the meshes in the given iterable will be joined with the first one.
    The first element of meshes will be modified and returned.
    """
    assert len(meshes) > 0, "Empty mesh list"
    for mesh in meshes[1:]:
        _aims.SurfaceManip.meshMerge(meshes[0], mesh)

    return meshes[0]


def apply_Talairach_to_mesh(mesh, dxyz, rotation, translation, flip=False):
    """Apply a talairach transformation to the given mesh.

    The Talairach parameters are the scaling vector, the rotation matrix and
    the translation vector of the Talairach transform.

    The flip parameter allows to flip from one brain hemisphere to to the other

    The operations are applied in the following order
    1. scale
    2. Talairach transform
    3. flip

    Return: a new mesh
    """

    dxyz = dxyz.copy()

    # Rescale mesh
    rescale_mesh(mesh, dxyz)

    # apply Talairach transform
    transform_mesh_inplace(mesh, rotation, translation)

    if flip:
        flip_mesh(mesh)

    return mesh