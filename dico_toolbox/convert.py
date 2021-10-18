# from scipy.ndimage.measurements import minimum
from . import bucket as _bucket
from . import mesh as _mesh
import os
import tempfile
from soma import aims as _aims
from soma import aimsalgo as _aimsalgo

from scipy import ndimage as _ndimage

import numpy as np
import shutil as _shutil
import logging
from ._dev import _deprecation_alert_decorator
log = logging.getLogger(__name__)


def ndarray_to_volume_aims(ndarray):
    """Create a new volume from the numpy ndarray.
    The array is first converted to Fortran ordering,
    as requested by the Volume constructor

    :param ndarray: the volume data
    :type ndarray: numpy.ndarray
    :return: an Aims Volume object containing the same data as ndarray
    :rtype: aims.Volume
    """
    assert(ndarray.dtype in [np.int16, np.int32,
           np.float64]), "Wrong data type"
    ndarray.reshape(*ndarray.shape, 1)
    return _aims.Volume(np.asfortranarray(ndarray))


def bucketMAP_aims_to_ndarray(bck_map, scaled=True):
    """Transform the first element of an aims bucket MAP into numpy array.
    NOTE: Unless scaled=True, the voxel size stored in the bucket's header
          is not taken into considesation here. The unscaled coordinates are returned.

    :param bck_map: aims bucket MAP
    :type aims_bucket: soma.aims.BucketMap_VOID
    :param scaled: if True the coordinates are scaled according to the voxel size.
    :return: bool
    :rtype: numpy.ndarray
    """

    assert type(bck_map) in [_aims.BucketMap_VOID, _aims.rc_ptr_BucketMap_VOID]

    if scaled:
        dxyz = bck_map.header()['voxel_size'][:3]
    else:
        dxyz = np.ones(3)

    return bucket_aims_to_ndarray(bck_map[0], voxel_size=dxyz)


def bucket_aims_to_ndarray(aims_bucket, voxel_size=(1, 1, 1)):
    """Transform an aims bucket into numpy array.

    :param aims_bucket: aims bucket object
    :type aims_bucket: soma.aims.BucketMap_VOID.Bucket
    :rtype: numpy.ndarray
    """

    if isinstance(aims_bucket, _aims.BucketMap_VOID):
        raise ValueError("The argument is a BucketMap.")

    assert isinstance(aims_bucket, _aims.BucketMap_VOID.Bucket)
    voxel_size = np.array(voxel_size)

    if aims_bucket.size() > 0:
        v = np.empty((aims_bucket.size(), len(aims_bucket.keys()[0].list())))
        for i, point in enumerate(aims_bucket.keys()):
            v[i] = point.arraydata()*voxel_size
    else:
        log.debug("Empty bucket! This can be a source of problems...")
        v = np.empty(0)
    return v


def bucket_numpy_to_bucket_aims(ndarray):
    """Transform a (N,3) ndarray into an aims BucketMap_VOID.
    The coordinates in the input array are casted to int.
    """

    # TODO: set the voxel_size in the aims bucket

    assert ndarray.shape[1] == 3, " ndarray shape must be (N,3)"

    if ndarray.dtype != int:
        ndarray = ndarray.astype(int)

    # create aims bucketmap instance
    bck = _aims.BucketMap_VOID()
    b0 = bck[0]

    # fill the bucket
    for x, y, z in ndarray:
        b0[x, y, z] = 1

    return bck


def volume_to_ndarray(volume):
    """Transform aims volume in numpy array.

    Takes the first element for every dimensions > 3.

    Args:
        volume (aims.volume): aims volume
    """
    # remove all dimensions except the 3 first
    # take element 0 for the others
    try:
        # aims VOlume and numpy array have shape
        if len(volume.shape) > 3:
            volume = volume[tuple(3*[slice(0, None)] + [0]
                                  * (len(volume.shape)-3))]
    except AttributeError:
        # aims.AimsData does not have shape
        # but it is always 3D
        volume = volume[:, :, :, 0]
    return volume[:]


def _volume_size_from_numpy_bucket(bucket_array, pad):
    a = bucket_array
    # the minimum and maximum here make sure that the voxels
    # are in the absolute coordinates system of the bucket
    # i.e. the volume always include the bucket origin.
    # This is the behaviour of AIMS
    # this also makes the volume bigger and full with zeros
    v_max = np.maximum((0, 0, 0), a.max(axis=0))
    v_min = np.minimum((0, 0, 0), a.min(axis=0))
    v_size = np.ceil(abs(v_max - v_min) + 1 + pad*2).astype(int)
    return v_size, v_min


def _point_to_voxel_indices(point):
    """transform the point coordinates into a tuple of integer indices.

    Args:
        point (Sequence[numeric]): point coordinates

    Returns:
        numpy.ndarray of type int: indices
    """
    return np.round(point).astype(int)


def bucket_numpy_to_volume_numpy(bucket_array, pad=0, side=None):
    """Transform a bucket into a 3d boolean volume.
    Input and output types are numpy.ndarray

    Return: a Tuple (volume, offset)
    the offset is a vector specifing the position of the origin in the volume
    """

    v_size, offset = _volume_size_from_numpy_bucket(bucket_array, pad)

    vol = np.zeros(np.array(v_size))

    for p in bucket_array:
        x, y, z = _point_to_voxel_indices((p-offset)+pad)
        vol[x, y, z] = 1

    return vol, offset


def bucket_numpy_to_volume_aims(bucket_array, pad=0):
    """Transform a bucket into a 3d binary volume."""

    v_size, v_min = _volume_size_from_numpy_bucket(bucket_array, pad)

    vol = _aims.Volume(*v_size, dtype='int16')
    vol.fill(0)
    avol = volume_to_ndarray(vol)

    for p in bucket_array:
        x, y, z = _point_to_voxel_indices(p-v_min+pad)
        avol[x, y, z] = 1

    return vol


def bucket_aims_to_volume_aims(aims_bucket, pad=0):
    """Transform a bucket into a 3d binary volume."""
    # TODO : transfer metadata
    # e.g. the dxyz is kept in the aims volume

    log.debug("The voxel size is lost in the conversion.")

    abucket = bucket_aims_to_ndarray(aims_bucket)
    return bucket_numpy_to_volume_aims(abucket, pad=pad)


def bucketMap_aims_to_rc_ptr_Volume_aims(bucketMap, volume_type=_aims.rc_ptr_Volume_S16):
    """Convert a bucketMap into an aims Volume.

    volume_type must be of type aims.rc_ptr_Volume_*.
    In order to get an aims.Volume_* use the get() method of the re_ptr object
    """
    c = _aims.Converter(intype=bucketMap, outtype=_aims.rc_ptr_Volume_S16)
    rc_ptr = c(bucketMap)
    return rc_ptr


def bucket_aims_to_volume_numpy(aims_bucket):
    """Transform a bucket into a 3D binary ndarray volume.

    Return: a Tuple (volume, offset)
    the offset is a vector specifing the position of the origin in the volume
    """

    abucket = bucket_aims_to_ndarray(aims_bucket)
    volume, offset = bucket_numpy_to_volume_numpy(abucket)
    return volume, offset


def volume_to_bucket_numpy(volume):
    """Transform a binary volume into a bucket.
    The bucket contains the coordinates of the non-zero voxels in volume.

    Args:
        volume (numpy array | aims volume): 3D image

    Returns:
        numpy.ndarray: bucket of non-zero points coordinates
    """
    return np.argwhere(volume_to_ndarray(volume))


def volume_to_bucket_aims(volume):
    return np.argwhere(volume_to_ndarray(volume))


def add_border(x, thickness, value):
    """add borders to volume (numpy)"""
    t = thickness
    x[:t, :, :] = value
    x[-t:, :, :] = value

    x[:, :t, :] = value
    x[:, -t:, :] = value

    x[:, :, :t] = value
    x[:, :, -t:] = value

    return x


# def volume_to_mesh(volume, smoothingFactor=2.0, aimsThreshold='96%',
#                    deciMaxError=0.5, deciMaxClearance=1.0, smoothIt=20, translation=(0, 0, 0)):
#     """Generate the mesh of the input volume.
#     WARNING: This function directly call some BrainVisa command line tools via os.system calls.

#     Args:
#         volume (nparray or pyaims volume): The input volume.
#         smoothingFactor (float, optional): Standard deviation of the 3D isomorph Gaussian filter of the input volume.
#         aimsThreshold (float or str) : First threshold value. All voxels below this value are not considered.
#             The threshold can be expressed as:
#             - a float, representing the threshold intensity
#             - a percentage (e.g. "95%") which represents the percentile of low-value pixel to eliminate.
#         deciMaxError (float) : Maximum error distance from the original mesh (mm).
#         deciMaxClearance (float) : Maximum clearance of the decimation.
#         smoothIt (int) : Number of mesh smoothing iteration.
#         translation (vector or 3 int) : translation to apply to the calculated mesh

#     Returns:
#         aims Mesh : the mesh of the inputn volume.
#     """

#     log.debug("volume_to_mesh:")

#     v = volume[:]
#     # normalize
#     v = ((v - v.min())/(v.max()-v.min())*256).astype(np.float)

#     # temporary directory
#     dirpath = tempfile.mkdtemp()

#     fname = "temp_initial.ima"
#     # write volume to file
#     _aims.write(ndarray_to_volume_aims(v), f"{dirpath}/{fname}")

#     # Gaussian blur
#     if smoothingFactor > 0:
#         out_fname = "temp_smoothed.ima"
#         gaussianSmoothCmd = f'AimsGaussianSmoothing -i {dirpath}/{fname} -o {dirpath}/{out_fname} -x {smoothingFactor} -y {smoothingFactor} -z {smoothingFactor}'
#         log.debug(gaussianSmoothCmd)
#         os.system(gaussianSmoothCmd)
#         fname = out_fname

#     # Threshold
#     # read the blurred volume values and calculate the threshold
#     v = _aims.read(f"{dirpath}/{fname}")[:]
#     nonzero_voxels = v[v > 0].flatten()
#     if type(aimsThreshold) == str:
#         # the threshold is a string
#         if aimsThreshold[-1] == '%':
#             # use the percentage value
#             q = float(aimsThreshold[:-1])
#             aimsThreshold = np.percentile(nonzero_voxels, q)
#         else:
#             raise ValueError(
#                 "aimsThreshold must be a float or a string expressing a percentage (eg '90%')")

#     out_fname = "temp_threshold.ima"
#     thresholdCmd = f"AimsThreshold -i {dirpath}/{fname} -o {dirpath}/{out_fname} -b -t {aimsThreshold}"
#     log.debug(thresholdCmd)
#     os.system(thresholdCmd)
#     fname = out_fname

#     # MESH
#     # Generate one mesh per interface (connected component?)
#     if smoothIt is not None and smoothIt is not 0:
#         smooth_arg = f"--smooth --smoothIt {smoothIt}"
#     else:
#         smooth_arg = ""

#     meshCmd = f'AimsMesh -i {dirpath}/{fname} -o {dirpath}/temp.mesh --decimation --deciMaxError {deciMaxError} --deciMaxClearance {deciMaxClearance} {smooth_arg}'
#     log.debug(meshCmd)
#     os.system(meshCmd)

#     # Concatenate the meshes
#     zcatCmd = f'AimsZCat  -i  {dirpath}/temp*.mesh -o {dirpath}/combined.mesh'
#     log.debug(zcatCmd)
#     os.system(zcatCmd)

#     mesh = _aims.read(f"{dirpath}/combined.mesh")

#     assert len(translation) == 3, "len(translation) must be 3"

#     if any(np.array(translation) != 0):
#         mesh = _mesh.shift_aims_mesh(
#             mesh, translation, scale=1)

#     # delete the temporary files
#     _shutil.rmtree(dirpath)

#     return mesh


def volume_to_mesh(vol, gblur_sigma=1, threshold="80%",
                   deciMaxError=1.0, deciMaxClearance=3.0,
                   deciReductionRate=99, smoothRate=0.4,
                   smoothIt=30, translation=(0, 0, 0)):
    """
    Calculate the mesh of the given volume with pyAims.

    Args:
        volume (nparray or aims Volume): The input volume.
        gblur_sigma (float, optional): Standard deviation of the 3D isomorph Gaussian filter of the input volume.
        threshold (float or str) : First threshold value. All voxels below this value are not considered.
            The threshold can be expressed as:
            - a float, representing the threshold intensity
            - a percentage (e.g. "95%") which represents the percentile of low-value pixel to eliminate.
        deciMaxError (float) : Maximum error distance from the original mesh (mm).
        deciMaxClearance (float) : Maximum clearance of the decimation.
        smoothIt (int) : Number of mesh smoothing iteration.
        translation (vector or 3 int) : translation to apply to the calculated mesh


    Return aims.Mesh
    """

    # transform aims.Volume into numpy
    vol = vol[:]

    assert len(vol.shape) == 3
    # convert to float
    vol = vol.astype(np.float64)

    # GBLUR
    gblur = _ndimage.gaussian_filter(vol, gblur_sigma, mode='constant', cval=0)

    # NORMALIZE
    gblur = (gblur - gblur.min())/(gblur.max() - gblur.min())

    # THRESHOLD
    # NOTE: aims mesher only works with rc_ptr, therefore do not use numpy here
    # threshold = (gblur > threshold).astype(np.int16)
    nonzero_voxels = gblur[gblur > 0].flatten()
    if type(threshold) == str:
        # the threshold is a string
        if threshold[-1] == '%':
            # use the percentage value
            q = float(threshold[:-1])
            threshold = np.percentile(nonzero_voxels, q)
        else:
            raise ValueError(
                "aimsThreshold must be a float or a string expressing a percentage (eg '90%')")

    vol_16 = _aims.Volume_S16((1000*gblur).astype(np.int16))
    thresholder = _aims.AimsThreshold(
        _aims.AIMS_GREATER_OR_EQUAL_TO, threshold*1000, dtype=vol_16)
    thresh_vol = thresholder.bin(vol_16)

    # mesh
    m = _aimsalgo.Mesher()
    m.setDecimation(
        # deciReductionRate
        deciReductionRate,
        # deciMaxClearance
        deciMaxClearance,
        # deciMaxError
        deciMaxError,
        # deciFeatureAngle
        180)
    m.setSmoothing(
        # smoothType
        0,
        # nIteration
        smoothIt,
        # smoothRate
        smoothRate)

    mesh_dict = m.doit(thresh_vol)

    mesh_dict_reduced = {k: _mesh.join_meshes(v) for k, v in mesh_dict.items()}
    mesh = _mesh.join_meshes(list(mesh_dict_reduced.values()))

    # TRANSLATION
    assert len(translation) == 3, "len(translation) must be 3"
    if any(np.array(translation) != 0):
        mesh = _mesh.shift_aims_mesh(
            mesh, translation, scale=1)

    return mesh


def bucket_to_mesh(bucket, gblur_sigma=0, threshold=1,
                   deciMaxError=1.0, deciMaxClearance=3.0,
                   deciReductionRate=99, smoothRate=0.4,
                   smoothIt=30, translation=(0, 0, 0), flip=False):
    """Generate the mesh of the input bucket.
    WARNING: This function directly call some BrainVisa command line tools via os.system calls.

    Args:
        bucket (nparray or pyaims bucket): The input bucket.
        flip (bool), flip the x coordinate of the bucket before meshing

    see volume_to_mesh for a description of the other arguments

    Returns:
        aims Mesh : the mesh of the inputn volume.
    """

    if isinstance(bucket, _aims.BucketMap_VOID.Bucket):
        bucket = bucket_aims_to_ndarray(bucket)
    elif isinstance(bucket, _aims.BucketMap_VOID):
        raise ValueError("Input is a BucketMap, not a bucket.")

    if flip:
        bucket = _bucket.flip_bucket(bucket)

    if any([x-int(x) != 0 for x in bucket[:].ravel()]):
        log.warn(
            "This bucket's coordinates are not integers. Did you apply any transformation to it?")

    volume, offset = bucket_numpy_to_volume_numpy(bucket)
    translation += offset

    return volume_to_mesh(volume, gblur_sigma=gblur_sigma, threshold=threshold, smoothRate=smoothRate,
                          deciMaxError=deciMaxError, deciMaxClearance=deciMaxClearance, smoothIt=smoothIt,
                          translation=translation, deciReductionRate=deciReductionRate)


def buket_to_aligned_mesh(*args, **kwargs):
    raise SyntaxError(
        "This function is deprecated due to misspelling of 'bucket', please use bucket_to_aligned_mesh")


def bucket_to_aligned_mesh(raw_bucket, talairach_dxyz, talairach_rot, talairach_tr, align_rot, align_tr, flip=False, **kwargs):
    """Generate the mesh of the given bucket.

    The mesh is transformed according to the given rotations and translations.

    The Talairach parameters are the scaling vector, the rotation matrix and the translation vector of the Talairach transform.
    The align paramenters are the rotation matrix and translation vector of the alignment with the central subjet.

    The kwargs are directly passed to cld.aims_tools.bucket_to_mesh().
    """

    # Generate mesh
    mesh = bucket_to_mesh(raw_bucket, flip=flip, **kwargs)

    dxyz = talairach_dxyz.copy()

    # Rescale mesh
    _mesh.rescale_mesh(mesh, dxyz)

    # apply Talairach transform
    M1 = get_aims_affine_transform(talairach_rot, talairach_tr)
    _aims.SurfaceManip.meshTransform(mesh, M1)

    # apply alignment transform
    M2 = get_aims_affine_transform(align_rot, align_tr)
    _aims.SurfaceManip.meshTransform(mesh, M2)

    return mesh


def get_aims_affine_transform(rotation_matrix, transltion_vector):
    """Get an aims AffineTransformation3d from rotation matrix and rotation vector"""
    m = np.hstack([rotation_matrix, transltion_vector.reshape(-1, 1)])
    M = _aims.AffineTransformation3d()
    M.fromMatrix(m)
    return M


# ALIASES FOR DEPRECATED FUNCTIONS
@_deprecation_alert_decorator(use_instead=ndarray_to_volume_aims)
def ndarray_to_aims_volume(*args, **kwargs): pass
