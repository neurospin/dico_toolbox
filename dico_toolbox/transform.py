import numpy as _np
from soma import aims as _aims
from soma import aimsalgo as _aimsalgo


def transform_bucket_resample(bucket_map: _aims.rc_ptr_BucketMap_VOID,
                              trm: _aims.AffineTransformation3d,
                              trm_inverse: _aims.AffineTransformation3d = None):
    """
    Apply an affine transformation to a bucket Map and resample.

    See the documentation of soma.aimsalgo.resampleBucket() for more details
    """

    if trm_inverse is None:
        trm_inverse = trm.inverse()

    return _aimsalgo.resampleBucket(bucket_map, trm, trm_inverse)


def transform_datapoints(
            data_points: _np.ndarray,
            dxyz: _np.ndarray=None,
            affine_matrix: _np.ndarray=None,
            rotation_matrix: _np.ndarray=None,
            translation_vector: _np.ndarray=None,
            flip: bool = False) -> _np.ndarray:
    """Transform the data_points.
    Return a new transformed array without modifing the input data.

    The datapoint are scaled according to dxyz, then rotated with rotation_matrix and
    translated by translation_vector.

    if a 4x4 affine transformation matrix is specified, the rotation matrixn and translation vectors are
    calculated from it and therefore the corresponding parameters are ignored.

    This means that dxyz does not rescale the translation vector.

    NOTE: No resampling is done, therefore the result might not have the same topology as the input
    (namely, holes could be introduced in the process.)

    If flip is True, the x coordinates are inverted after the transformation (x --> -x)
    """

    if affine_matrix is not None:
        assert(affine_matrix.shape == (4,4)), "wrong matrix shape"
        rotation_matrix = affine_matrix[0:3,0:3]
        translation_vector = affine_matrix[0:3,3]

    tr_data_points = data_points.copy().astype(float)

    # Rescale
    if dxyz is not None and not _np.array_equal(dxyz,(1,1,1)):
        dxyz = _np.array(dxyz).reshape(1,3) #ensure shape
        tr_data_points *= dxyz

    # Rotation
    if (rotation_matrix is not None) and not _np.array_equal(rotation_matrix, _np.eye(3)):
        tr_data_points = _np.dot(tr_data_points, rotation_matrix.T)

    # Translation
    if (translation_vector is not None) and not _np.array_equal(translation_vector, _np.zeros(3)):
        translation_vector = _np.array(translation_vector).reshape(1,3) #ensure shape
        tr_data_points += translation_vector 

    if flip:
        tr_data_points[:,0] *= -1

    return tr_data_points


def get_aims_affine_transform(rotation_matrix, transltion_vector):
    """Get an aims AffineTransformation3d from rotation matrix and rotation vector"""
    m = _np.hstack([rotation_matrix, transltion_vector.reshape(-1, 1)])
    M = _aims.AffineTransformation3d()
    M.fromMatrix(m)
    return M