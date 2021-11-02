from genericpath import exists
import os.path as op
import os
import subprocess
from warnings import warn
import re
import dico_toolbox as dtb
import shutil


# Links to the data for each release
URLS = {
    "0.1.0": "https://cloud.bablab.fr/index.php/s/FiHQsaPajZJSdRq/download"
}


# Name of the environment variable used to customize where the data are saved
ENV_PATH_VAR = 'DICO_TOOLBOX_DATA_DIR'
ENV_SOURCE_PATH_VAR = 'DICO_TOOLBOX_SOURCE_DIR'

# Defaul location of the test data
DEFAULT_DATA_PATH = op.realpath(op.join(op.split(__file__)[0], '..',
                                        'dico_toolbox_tests', 'test_data'))


def _check_version(version=None, use_default=True) -> str:
    """ Check if data are available for the version.

    Parameters
    ----------
    version: str or None (opt.)
        If None, the package version is used.

    use_default: bool (opt.)
        If no link ins specified in URLS for the given version:
            *if use_default is True: the link of the highest version is return
            *else an error is raised
    Return
    ------
    version: str
    """
    if version is not None and not isinstance(version, str):
        raise ValueError("If specified, version must be a valid string. {} given".
                         format(type(version)))

    version = dtb.__version__ if version is None else version

    if not version in URLS.keys():
        if use_default:
            # Use the last release by default
            new_version = list(sorted(URLS.keys()))[-1]
            warn('No test data URL found for version "{}". Using data of version "{}".'.
                 format(version, new_version))
            version = new_version
        else:
            raise ValueError('No test data defined for version "{}". '
                             'Available test data only for versions: {}'.
                             format(version, ', '.join(URLS.keys())))
    return version


# Regex pattern for URLs
URL_RE = re.compile(
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")


def _is_url(string) -> bool:
    """ Return True if string contains an URL. """
    return URL_RE.fullmatch(string) is not None


def data_directory(version=None) -> str:
    """ Return the path of the test data directory.

    If the environment variable is defined, use it, otherwise a default path is
    used.
    """
    if os.getenv(ENV_PATH_VAR):
        # User defined
        root = os.getenv(ENV_PATH_VAR)
        warn("Using environment defined data directory: {}".format(root))
    else:
        # Default
        root = DEFAULT_DATA_PATH

    if version is None:
        version = _check_version()

    return op.join(root, version)


def load_data(source=None, version=None, path=None, force=False) -> str:
    """ Load test data and return the test data path.

    Parameters:
    -----------
    source: None or str (opt.)
        Use a custom source (path to directory, path to a .zip file or url)
        instead of the hard coded one.

    version: None or str (opt.)
        Specify a version. By default, the current package version is used.

    path: None or str (opt.)
        Specify a custom destination directory. By default, data are saved
        the directory given by the environnment variable or (if not set) by
        the code.

    force: bool (opt.)
        If True, erase already existing data and rewrite them.
        Default is False.

    Return
    ------
    path: str
        Path to the test data.
    """
    if source is None and ENV_SOURCE_PATH_VAR in os.environ:
        source = os.environ[ENV_SOURCE_PATH_VAR]
        if source is not None:
            warn("Using environment defined source: {}".format(source))

    # If a source is specified:
    #   if it is a valid path: copy the data only if force is True otherwise, return the source path
    #   if it is an URL: download the data
    # If an existing version is specified, warn the user.
    if source is not None:
        try:
            version = _check_version(version, use_default=False)
        except ValueError:
            pass
        if version in URLS.keys():
            warn('Replacing default testing data for version {} by data from {}'.
                 format(version, source))

        if op.isdir(source) and not force:
            return source
    else:
        version = _check_version(version)
        source = URLS[version]

    path = data_directory(version) if path is None else path
    root = op.realpath(op.join(path, '..'))

    # If the direcotry already exist, if force is True, remove and erase old data
    # and re-download, else do nothing.
    if op.exists(path):
        if force:
            shutil.rmtree(path)
        else:
            return path

    os.makedirs(path)

    zip_file = op.realpath(op.join(path, "..", "{}.zip".format(version)))
    if _is_url(source):
        # Download .zip from source
        cmd = 'wget --no-check-certificate  --content-disposition  {} -O {} '. \
            format(source, zip_file)

        val = subprocess.call(cmd.split())
        if val or not op.exists(zip_file):
            os.remove(path)
            raise RuntimeError("An error occured while downloading test data from {} to {}.".
                               format(source, zip_file))
    elif op.isfile(source) and source.endswith('.zip'):
        # Copy .zip from a path
        val = subprocess.call("cp {} {}".format(source, zip_file).split())
        if val:
            shutil.rmtree(path)
            raise RuntimeError("An error occured while copying data from {} to {}.".
                               format(source, zip_file))
    elif op.isdir(source):
        # Copy data from path
        val = subprocess.call("cp -r {} {}".format(source, root).split())
        # Here, no need to unzip
        return path
    else:
        raise ValueError('Source is neither a URL, a path to a .zip file or a path to an'
                         'existing directory. "{}" given.'.format(source))

    # Unzip data
    val = subprocess.call("unzip -o {} -d {}".format(zip_file, root).split())
    if val:
        # If it failed, remove the data directory otherwise next time the function will
        # not retry downloading
        shutil.rmtree(path)
        raise RuntimeError("An error occured while decompressing test data from {} to {}.".
                           format(zip_file, path))
    os.remove(zip_file)
    return path


def bv_database() -> dtb.database.BVDatabase:
    return dtb.database.BVDatabase(op.join(load_data(), "bv_database"))
