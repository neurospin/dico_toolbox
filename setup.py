import setuptools
import os.path as op
import re
import logging as _logging

_log = _logging.getLogger(__name__)


def get_property(prop, project):
    lookup_file = '/__init__.py'
    result = re.findall(r'^{}\s*=\s*[\'"]([^\'"]*)[\'"]$'.format(
        prop), open(project + lookup_file).read(), re.MULTILINE)
    # re.findall always returns list
    if len(result) != 1:
        _log.warn("Alert: More than one occurrence of {} found in {}}".format([prop, project + lookup_file]))
    assert type(result[0]) == str
    return result[0]


try:
    from aims import soma
except:
    ImportError(
        "pyAims could not be imported. It makes no sense to install this package outside a brainvisa environment.")

with open(op.join(op.split(__file__)[0], "README.md"), "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='dico_toolbox',
    version=get_property('__version__', 'dico_toolbox'),
    description="A common toolbox to the FoldDico project",
    author='Marco Pascucci, Bastien Cagna',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='marpas.paris@gmail.com',
    url='',
    packages=['dico_toolbox'],
    install_requires=['numpy'],
    extras_require={
        'dev': [
            'pytest'
        ]
    },
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ]
)
