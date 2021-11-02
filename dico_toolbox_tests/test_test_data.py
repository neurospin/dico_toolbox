from dico_toolbox import test_data
import pytest
from dico_toolbox.test_data import ENV_SOURCE_PATH_VAR, _check_version, bv_database, data_directory, \
    _is_url, load_data, DEFAULT_DATA_PATH, ENV_PATH_VAR, ENV_SOURCE_PATH_VAR
import dico_toolbox as dtb
import os.path as op
import os
import shutil


def test_check_version():
    assert _check_version(use_default=False) == dtb.__version__

    with pytest.warns(UserWarning):
        assert _check_version(dtb.__version__ + "0") == dtb.__version__
        assert _check_version("3516854") == dtb.__version__

    with pytest.raises(ValueError):
        assert _check_version('999.0.1', use_default=False)


def test_data_directory():
    assert data_directory() == op.join(DEFAULT_DATA_PATH, _check_version())

    test_path = op.join("/tmp", "dtb_test_data")
    os.environ[ENV_PATH_VAR] = test_path
    assert data_directory() == op.join(test_path, _check_version())

    assert data_directory("my_data") == op.join(test_path, "my_data")


def test_is_url():
    assert _is_url("http://url.com") == True
    assert _is_url("www.url.com") == True
    assert _is_url("http://www.url.com") == True
    assert _is_url("abc") == False
    assert _is_url("http://") == False
    assert _is_url("/a/path") == False


def test_load_data():
    if ENV_PATH_VAR in os.environ:
        del os.environ[ENV_PATH_VAR]
    if ENV_SOURCE_PATH_VAR in os.environ:
        del os.environ[ENV_SOURCE_PATH_VAR]

    # Load data at default location
    dt_path = load_data()
    assert dt_path == data_directory()
    assert op.isdir(dt_path)

    os.environ[ENV_PATH_VAR] = op.join("/tmp", "dtb_toolbox", "test_data")
    path = load_data(source=dt_path)
    assert path == dt_path

    # Copy from default location to custom one
    os.environ[ENV_SOURCE_PATH_VAR] = dt_path
    cdt_path = load_data(force=True)
    assert cdt_path == op.join(os.environ[ENV_PATH_VAR], _check_version())
    assert op.isdir(cdt_path)
    assert len(os.listdir(cdt_path)) == len(os.listdir(dt_path))

    shutil.rmtree(op.realpath(op.join(dt_path, '..')))
    shutil.rmtree(os.environ[ENV_PATH_VAR])
    del os.environ[ENV_PATH_VAR]
    del os.environ[ENV_SOURCE_PATH_VAR]


def test_bv_database():
    assert type(bv_database()) == dtb.database.BVDatabase
