# [treesource] conversion of pyAims and numpy objects
# from scipy.ndimage.measurements import minimum
from . import bucket as _bucket
from . import mesh as _mesh
from . import transform as _transform
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


def bucket_numpy_to_bucketMap_aims(ndarray, voxel_size=(1, 1, 1)):
    """Transform a (N,3) ndarray into an aims BucketMap_VOID.
    The coordinates in the input array are casted to int.
    """

    # TODO: set the voxel_size in the aims bucket

    assert ndarray.shape[1] == 3, " ndarray shape must be (N,3)"

    if ndarray.dtype != int:
        ndarray = ndarray.astype(int)

    # create aims bucketmap instance
    bck_map = _aims.BucketMap_VOID()
    bck_map.setSizeXYZT(*voxel_size, 1)
    b0 = bck_map[0]

    # fill the bucket
    for x, y, z in ndarray:
        b0[x, y, z] = 1

    return bck_map


@_deprecation_alert_decorator(bucket_numpy_to_bucketMap_aims)
def bucket_numpy_to_bucket_aims(ndarray):
    pass


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


def volume_to_bucketMap_aims(volume, voxel_size=(1, 1, 1)):
    """Convert a volume (aims or numpy) into an AIMS bucket"""
    points_cloud = np.argwhere(volume_to_ndarray(volume))
    # add 4th dimension to the vozel size with a default size of 1
    return bucket_numpy_to_bucketMap_aims(points_cloud, voxel_size=voxel_size)


@_deprecation_alert_decorator(volume_to_bucketMap_aims)
def volume_to_bucket_aims(volume):
    pass


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
            - a float in [0,1], representing the normalized threshold intensity
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

    # === GBLUR ===
    gblur = _ndimage.gaussian_filter(vol, gblur_sigma, mode='constant', cval=0)

    # === NORMALIZE ===
    gblur = (gblur - gblur.min())/(gblur.max() - gblur.min())

    # === THRESHOLD ===
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

    MAX_VOXEL_VALUE = 1000
    threshold *= MAX_VOXEL_VALUE

    vol_16 = _aims.Volume_S16((MAX_VOXEL_VALUE*gblur).astype(np.int16))
    thresholder = _aims.AimsThreshold(
        _aims.AIMS_GREATER_OR_EQUAL_TO, np.int16(threshold), dtype=vol_16)
    thresh_vol = thresholder.bin(vol_16)

    # NOTE: I could not make the mesher work when tresholding with python
    # gblur *= MAX_VOXEL_VALUE
    # thresh_vol = np.array( gblur[gblur>threshold], dtype=np.int16, order='F')
    # thresh_vol = _aims.Volume_S16(thresh_vol)

    # === MESH ===
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

    # === JOIN MESHES ===
    mesh_dict_reduced = {k: _mesh.join_meshes(v) for k, v in mesh_dict.items()}
    mesh = _mesh.join_meshes(list(mesh_dict_reduced.values()))

    # === TRANSLATION ===
    assert len(translation) == 3, "len(translation) must be 3"
    if any(np.array(translation) != 0):
        mesh = _mesh.shift_aims_mesh(
            mesh, translation, scale=1)

    return mesh


def bucket_to_mesh(bucket, gblur_sigma=0, threshold=1,
                   deciMaxError=1.0, deciMaxClearance=3.0,
                   deciReductionRate=0, smoothRate=0.15,
                   smoothIt=30, translation=(0, 0, 0)):
    """Generate the mesh of the input bucket.
    WARNING: This function directly call some BrainVisa command line tools via os.system calls.

    Args:
        bucket (nparray or pyaims bucket): The input bucket.

    see volume_to_mesh for a description of the other arguments

    Returns:
        aims Mesh : the mesh of the inputn volume.
    """

    if isinstance(bucket, _aims.BucketMap_VOID.Bucket):
        bucket = bucket_aims_to_ndarray(bucket)
    elif isinstance(bucket, _aims.BucketMap_VOID):
        raise ValueError("Input is a BucketMap, not a bucket.")

    if any([x-int(x) != 0 for x in bucket[:].ravel()]):
        log.debug(
            "This bucket's coordinates are not integers. Did you apply any transformation to it?")

    volume, offset = bucket_numpy_to_volume_numpy(bucket)
    translation += offset

    mesh = volume_to_mesh(volume, gblur_sigma=gblur_sigma, threshold=threshold, smoothRate=smoothRate,
                          deciMaxError=deciMaxError, deciMaxClearance=deciMaxClearance, smoothIt=smoothIt,
                          translation=translation, deciReductionRate=deciReductionRate)

    return mesh


# ALIASES FOR DEPRECATED FUNCTIONS
@_deprecation_alert_decorator(use_instead=ndarray_to_volume_aims)
def ndarray_to_aims_volume(*args, **kwargs): pass
