from soma import aims as _aims
import numpy as _np

def rescale_mesh(mesh, dxyz):
    """Rescale a mesh by multiplying its vertices with the factors in dxyx.
    The rescaling is done in place."""
    for i in range(mesh.size()):
        mesh.vertex(i).assign(
            [_aims.Point3df(_np.array(x[:])*dxyz) for x in mesh.vertex(i)])


def flip_mesh(mesh, axis=0):
    """Flip the mesh by inverting the specified axis"""
    flip_v = _np.ones(3)
    flip_v[axis] = -1
    for i in range(mesh.size()):
        mesh.vertex(i).assign(
            [_aims.Point3df(_np.array(x[:])*flip_v) for x in mesh.vertex(i)])


def shift_aims_mesh(mesh, offset, scale=1):
    """Translate each mesh of a specified distance along an axis.

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
    shift_v = _np.zeros(3)
    shift_v[axis] = offset
    return shift_aims_mesh(mesh, shift_v, scale=scale)