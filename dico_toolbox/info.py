# -*- coding: utf-8 -*-

version_major = 0
version_minor = 1
version_micro = 2
version_extra = ''

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
__version__ = "%s.%s.%s%s" % (version_major,
                              version_minor,
                              version_micro,
                              version_extra)
CLASSIFIERS = [
    "Programming Language :: Python",
    "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    "Operating System :: OS Independent",
]


description = "A common toolbox to the FoldDico project"

# versions for dependencies
SPHINX_MIN_VERSION = '1.0'

# Main setup parameters
NAME = 'dico_toolbox'
PROJECT = 'dico_toolbox'
ORGANISATION = "neurospin"
MAINTAINER = "nobody"
MAINTAINER_EMAIL = "support@neurospin.info"
DESCRIPTION = description
URL = "https://github.com/neurospin/dico_toolbox"
DOWNLOAD_URL = "https://github.com/neurospin/dico_toolbox"
LICENSE = "CeCILL-B"
AUTHOR = 'Marco Pascucci, Bastien Cagna'
AUTHOR_EMAIL = 'marpas.paris@gmail.com'
PLATFORMS = "OS Independent"
PROVIDES = ["dico_toolbox", "dico_toolbox.cli", "dico_toolbox.anatomist"]
REQUIRES = ['numpy', 'tqdm']
EXTRA_REQUIRES = {
    "doc": ["sphinx>=" + SPHINX_MIN_VERSION],
    'dev': ['pytest']
}
ENTRYPOINTS = {
    'console_scripts': [
        'dtb_volume_to_point_cloud=dico_toolbox.cli.volume_to_point_cloud:main',
        'nb2md=dico_toolbox.cli.notebook2markdown:main'
    ],
}

brainvisa_build_model = 'pure_python'
