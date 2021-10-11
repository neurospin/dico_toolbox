import numpy as np
from soma import aims, aimsalgo
from scipy.spatial.transform import Rotation as _scipy_Rotation


def transform_bucket_resample(bucket_map: aims.rc_ptr_BucketMap_VOID,
                              trm: aims.AffineTransformation3d,
                              trm_inverse: aims.AffineTransformation3d = None):
    """
    Apply an affine transformation to a bucket Map and resample.

    See the documentation of soma.aimsalgo.resampleBucket() for more details
    """

    if trm_inverse is None:
        trm_inverse = trm.inverse()

    return aimsalgo.resampleBucket(bucket_map, trm, trm_inverse)


def transform_datapoints(data_points: np.ndarray, dxyz: np.ndarray, rotation_matrix: np.ndarray, translation_vector: np.ndarray, flip: bool = False) -> np.ndarray:
    """Transform the data_points.
    Return a new transformed array without modifing the input data.

    The datapoint are scaled according to dxyz, then rotated with rotation_matrix and
    translated by translation_vector.

    This means that dxyz does not rescale the translation vector.

    NOTE: No resampling is done, therefore the result might not have the same topology as the input
    (namely, holes could be introduced in the process.)

    If flip is True, the x coordinates are inverted (x --> -x)
    """

    tr_data_points = data_points.copy()

    # Rescale
    if dxyz is not None and not np.array_equal(dxyz,(1,1,1)):
        dxyz = np.array(dxyz).reshape(1,3) #ensure shape
        tr_data_points = tr_data_points*dxyz

    # Rotation
    if (rotation_matrix is not None) and not np.array_equal(rotation_matrix, np.eye(3)):
        rot = _scipy_Rotation.from_dcm(rotation_matrix)
        tr_data_points = rot.apply(tr_data_points)

    # Translation
    if (translation_vector is not None) and not np.array_equal(translation_vector, np.zeros(3)):
        translation_vector = np.array(translation_vector).reshape(1,3) #ensure shape
        tr_data_points += translation_vector 

    # tr_data_points = np.empty_like(data_points, dtype=float)

    # for i, point in enumerate(data_points):
    #     # multiply by scale factors
    #     point = point*dxyz

    #     if (rotation_matrix is not None) and not np.array_equal(rotation_matrix, np.eye(3)):
    #         # print("rotate", point)
    #         point = np.dot(rotation_matrix, point)

    #     # translate
    #     if (translation_vector is not None) and not np.array_equal(translation_vector, np.zeros(3)):
    #         # print("translate", point, translation_vector)
    #         point = point + translation_vector

    #     if flip:
    #         # print(point)
    #         point[0] = -point[0]

    #     # store
    #     tr_data_points[i] = point

    return tr_data_points
