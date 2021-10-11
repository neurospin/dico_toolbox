from soma import aims
from scipy.spatial.transform import Rotation
import numpy as np
import dico_toolbox as dt

def test_transform_datapoints():
    # zero is the kernel of any rotation
    datapoints = np.array(((0,0,0),))
    rot = Rotation.from_rotvec(np.array([np.pi/4, np.pi/3, np.pi/5])).as_dcm()
    tr = np.zeros(3)
    assert(np.array_equal(
        dt.transform.transform_datapoints(
            data_points = datapoints,
            dxyz = (1,1,1),
            rotation_matrix = rot,
            translation_vector = tr),
        datapoints))
    # test pure translation
    tr = np.array((-1,8, -3))
    rot = np.eye(3)
    assert(np.array_equal(
        dt.transform.transform_datapoints(
            data_points = datapoints,
            dxyz = (1,1,1),
            rotation_matrix = rot,
            translation_vector = tr),
        np.array([tr]))
        )
    # test identity
    datapoints = np.random.randint(-5,5,size=(5,3))
    rot = np.eye(3)
    tr = np.zeros(3)
    assert(np.array_equal(
    dt.transform.transform_datapoints(
        data_points = datapoints,
        dxyz = (1,1,1),
        rotation_matrix = rot,
        translation_vector = tr),
    datapoints)
    )
    # test rescale
    datapoints = np.array(((1,1, -1),))
    rot = np.eye(3)
    tr = np.zeros(3)
    dxyz = np.array((0.5,2,3))
    assert(np.array_equal(
    dt.transform.transform_datapoints(
        data_points = datapoints,
        dxyz = dxyz,
        rotation_matrix = rot,
        translation_vector = tr),
    datapoints*dxyz)
    )
    # compare rotation with scipy
    datapoints = np.random.randint(-5,5,size=(5,3))
    rot = Rotation.from_rotvec(np.array([np.pi/4, np.pi/3, np.pi/5]))
    tr = np.zeros(3)
    assert(np.allclose(
    dt.transform.transform_datapoints(
        data_points = datapoints,
        dxyz = (1,1,1),
        rotation_matrix = rot.as_dcm(),
        translation_vector = tr),
    rot.apply(datapoints))
    )