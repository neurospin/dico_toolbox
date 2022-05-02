import setuptools
import os.path as op
import os
import logging as _logging

_log = _logging.getLogger(__name__)

try:
    from soma import aims
except:
    ImportError(
        "pyAims could not be imported. It makes no sense to install this package outside a brainvisa environment.")

with open(op.join(op.split(__file__)[0], "README.md"), "r") as fh:
    long_description = fh.read()

release_info = {}
python_dir = os.path.dirname(__file__)
with open(os.path.join(python_dir, "dico_toolbox", "info.py")) as f:
    code = f.read()
    exec(code, release_info)


setuptools.setup(
    name=release_info['NAME'],
    version=release_info['__version__'],
    description=release_info['DESCRIPTION'],
    author=release_info['AUTHOR'],
    author_email=release_info['AUTHOR_EMAIL'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=release_info['URL'],
    packages=setuptools.find_packages(),
    install_requires=release_info["REQUIRES"],
    classifiers=release_info["CLASSIFIERS"],
    extras_require=release_info['EXTRA_REQUIRES'],
    entry_points=release_info['ENTRYPOINTS'],

)
