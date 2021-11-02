import setuptools
import os.path as op
import re


def get_property(prop, project):
    result = re.search(
        r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
    return result.group(1)


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
