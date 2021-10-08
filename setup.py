import setuptools

try:
    from aims import soma
except:
    ImportError("pyAims could not be imported. It makes no sense to install this package outside a brainvisa environment.")

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='dico_toolbox',
                 version='0.1.0',
                 description="A common toolbox to the FolDico project",
                 author='Marco Pascucci',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 author_email='marpas.paris@gmail.com',
                 url='',
                 packages=['dico_toolbox'],
                 install_requires=['numpy'],
                 classifiers=[
                     "Programming Language :: Python",
                     "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
                     "Operating System :: OS Independent",
                 ]
                 )
