Tutorials
==========


Database - Found file path in a BrainVISA database
--------------------------------------------------

How to perform a query
^^^^^^^^^^^^^^^^^^^^^^
The query is done by the get() methods which list all files that have been scanned during the creation of
the BVDatabase object and that match the parameters set by all the given key/value(s) pairs.
Here is a demo of how to find all the left skeletons of a subject:

.. code-block:: python

    from dico_toolbox.database import BVDatabase

    # Initialize the database object and scan files
    db = BVDatabase('/path/to/the/brainvisa/database')

    # List the subject names
    subject_names = db.list_all('subject')

    # Get all left skeletons of the first subject
    skeletons = db.get(subject=subject_names[0], segmentation="skeleton", hemisphere="left")


Using file path templates
^^^^^^^^^^^^^^^^^^^^^^^^^
For large, the scanning processing could be too long. An other way to find files path is to use path templates.
The query is done the same way as before but use get_from_template() and give a path template where some variable
part are specified by using a tag like "[variable_name]".

.. code-block:: python

    # By specifying use_template=True, no file scan will be performed
    # Note that as no scan has been performed, we can not use the .list_all() method.
    db = BVDatabase('/path/to/the/brainvisa/database')

    # General template for any segmentation ouput of Morphologist
    seg_template = "[center]/[subject]/t1mri/[acq]/[ana]/segmentation/[hemi][segtype]_[subject].nii*"

    # Skeleton of sub-01 and sub-02
    skeletons = db.get_from_template(seg_template, segtype='skeleton', 
                                     subject=['sub-01', 'sub-02'], hemi='L')

    # Or use directly predefined templates
    skeletons = db.get_from_template("morphologist_segmentation", type='skeleton', 
                                     subject=['sub-01', 'sub-02'], hemi='L')


Graphs
------