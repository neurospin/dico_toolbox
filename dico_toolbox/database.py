import os.path as op
from os import listdir
from typing import Sequence, SupportsComplex
from collections.abc import Sequence
from glob import glob


def create_test_database():
    db_path = op.abspath(op.join(__file__, "..", "..",
                                 "dico_toolbox_tests", "test_data", "database"))
    return BVDatabase(db_path)


def infer_file_type(fpath, attributes):
    """ Infer Axon file type from the path and attributes """
    # TODO: list file type somewhere
    if attributes['extension'] == '.arg':
        return "graph"
    return "unkown"


def extend_templates(templates, default_value=None, start_tag="[", end_tag="]", **kwargs):
    """ """
    if not isinstance(templates, Sequence):
        templates = [templates]

    if default_value is not None:
        # If specified, replace unused tag by the default value
        used_keys = list(kwargs.keys())
        unused_keys = set()
        for template in templates:
            split = template.split(start_tag)
            for sp in split:
                ssplit = sp.split(end_tag)
                if len(ssplit) > 1 and not ssplit[0] in used_keys:
                    unused_keys.add(ssplit[0])
        for template in templates:
            for key in unused_keys:
                template.replace(start_tag + key + end_tag, default_value)

    # Then list all possibilities
    for k in used_keys:
        tag = start_tag + k + end_tag
        if not isinstance(kwargs[k], Sequence):
            kwargs[k] = [kwargs[k]]
        for template in templates:
            if tag in template:
                for val in kwargs[k]:
                    templates.append(template.replace(
                        start_tag + k + end_tag, val))
                # Remove the old template (which still have the original tag)
                templates.remove(template)

    return templates


class BVDatabase:
    """

        Query system
        ============
        If kwargs element is a:
            - empty Sequence: all the files that have any value for this attribute are matching
            - value: all the files that have this value for this attribute are matching
            - Sequence: all the files that have one of the values for this attribute are matching
        Files must match all kwargs to be listed.

        Example
        =======
        '''python
            db = BVDatabase("/path/to/the/database")
            # Get the path of the left white mesh of trucmuche
            wmesh_path = db.get(subject='trucmuche', mesh='white', hemi='left)

            # Get all the graph
            graph = db.get(type="graph")
        '''
    """

    def __init__(self, path: str, use_templates=False):
        if not op.isdir(path):
            raise IOError(
                "The database path must point to an existing directory.")

        self.path = path
        self.use_templates = use_templates

        self.allowed_extensions = [
            ".APC", ".arg", ".csv", ".gii", ".json", ".nii", ".nii.gz", ".trm"]

        self.files = []
        self.files_attributes = []
        self.attributes = {}

        if not use_templates:
            # Expect output as:
            # db/center/subject/acqusition/analysis/segmentation
            # db/center/subject/acqusition/analysis/folds
            # TODO: add unscan _attributes?
            # FIXME: analysis cannot be listed as we do not go into the foldeer to list files
            self.unscan_paths = self._scan_subdirectories(
                self.path, ["center", "subject", "modality", "acquisition", "analysis"])

            self._scan_morphologist_analyses()

    def _add_file(self, path, **kwargs):
        if not op.isfile(path):
            raise ValueError("{} is not a file".format(path))
        if path in self.files:
            raise ValueError("{} already listed".format(path))

        _, ext = op.splitext(path)
        if ext == ".gz":
            ext = '.' + '.'.join(op.split(path)[1].split('.')[-2:])
        if ext not in self.allowed_extensions:
            return
        kwargs['extension'] = ext

        # TODO: use .minf to get more attributes?
        self.files.append(path,)
        self.files_attributes.append(kwargs)
        self.files_attributes[-1]['type'] = infer_file_type(path, kwargs)
        for k in kwargs:
            if k not in self.attributes.keys():
                self.attributes[k] = [kwargs[k]]
            elif kwargs[k] not in self.attributes[k]:
                self.attributes[k].append(kwargs[k])

    def _scan_subdirectories(self, path, levels, **kwargs):
        not_scanned_paths = []
        sub_kwargs = kwargs.copy()
        for item in listdir(path):
            item_path = op.join(path, item)
            if op.isdir(item_path):
                if item[0] is not '.':
                    sub_kwargs[levels[0]] = item
                    if len(levels) > 1:
                        self._scan_subdirectories(
                            item_path, levels[1:], **sub_kwargs)
                    else:
                        not_scanned_paths.append(item_path)
            else:
                self._add_file(item_path, **kwargs)
        return not_scanned_paths

    def _scan_morphologist_analyses(self, modality="t1mri"):
        # Look for Morphologist outputs
        for center in self.list_all('center'):
            for sub in self.list_all('subject', center=center, modality=modality):
                for acq in self.list_all('acquisition', center=center, subject=sub, modality=modality):
                    for ana in listdir(op.join(self.path, center, sub, modality, acq)):
                        # for ana in self.list_all('subject', center=center, subject=sub, modality="t1mri", acquisition=acq):
                        ana_path = op.join(
                            self.path, center, sub, modality, acq, ana)
                        seg_path = op.join(ana_path, "segmentation")
                        mesh_path = op.join(seg_path, "mesh")
                        fold_path = op.join(ana_path, "folds")
                        if op.isdir(seg_path):
                            for f in listdir(seg_path):
                                fpath = op.join(seg_path, f)
                                if op.isfile(fpath):
                                    # [hemi][seg_type]_[subject].[extension]
                                    fname, _ = op.splitext(f)
                                    seg_type = fname[:-len(sub)-1]
                                    hemi = f[0]

                                    if hemi in ['L', 'R']:
                                        # cortex, grey_white,, gw_interface, roots, skeleton
                                        hemi = 'left' if hemi == 'L' else 'right'
                                        self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                       acquisition=acq, analysis=ana, segmentation=seg_type,
                                                       hemisphere=hemi)
                                    else:
                                        # brain, head, skull_stripped, voronoi
                                        self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                       acquisition=acq, analysis=ana, segmentation=seg_type)

                            if op.isdir(mesh_path):
                                for f in listdir(mesh_path):
                                    fpath = op.join(mesh_path, f)
                                    if op.isfile(fpath):
                                        # [subject]_[hemi][seg_type].[extension]
                                        fname, _ = op.splitext(f)
                                        mesh_type = fname[len(sub)+1:]
                                        hemi = mesh_type[0]

                                        if hemi in ['L', 'R']:
                                            # white, hemi
                                            mesh_type = mesh_type[1:]
                                            hemi = 'left' if hemi == 'L' else 'right'
                                            self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                           acquisition=acq, analysis=ana, mesh=mesh_type,
                                                           hemisphere=hemi)
                                        else:
                                            # head
                                            self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                           acquisition=acq, analysis=ana, mesh=mesh_type)

                        if op.isdir(fold_path):
                            for version in listdir(fold_path):
                                fold_subpath = op.join(fold_path, version)

                                for f in listdir(mesh_path):
                                    fpath = op.join(fold_subpath, f)
                                    if op.isfile(fpath):
                                        # [hemi][subject]_[seg_type].[extension]
                                        fname, _ = op.splitext(f)
                                        seg_type = fname[len(sub)+1:]
                                        hemi = fname[0]

                                        if hemi in ['L', 'R']:
                                            # sulcivoronoi (also a segmentation file)
                                            seg_type = seg_type[1:]
                                            hemi = 'left' if hemi == 'L' else 'right'
                                            self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                           acquisition=acq, analysis=ana, segmentation=seg_type,
                                                           hemisphere=hemi)
                                        else:
                                            # ?
                                            self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                           acquisition=acq, analysis=ana, mesh=mesh_type)
                                    else:
                                        session = f
                                        for f in listdir(mesh_path):
                                            fpath = op.join(
                                                mesh_path, session, f)
                                            if op.isfile(fpath) and f[-4:] == ".arg":
                                                # [hemi][subject]_[session].arg
                                                hemi = fname[0]

                                                if hemi in ['L', 'R']:
                                                    hemi = 'left' if hemi == 'L' else 'right'
                                                    self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                                   acquisition=acq, analysis=ana, hemisphere=hemi,
                                                                   graph_version=version, graph_session=session)

    def list_all(self, attribute_name: str, **kwargs):
        """ List all attribute_name attribute for files that match kwargs specificiation.

            Parameters
            ==========
            attribute_name: str
                Files attribute name to check. (Example: "center", "acquisition", "extension", "mesh",...)

            Return
            ======
            The list of different values seen for attribute_name

            Example
            =======
            >>>subject = db.list_all("subject", center="center1")
        """
        for k in kwargs.keys():
            if not isinstance(kwargs[k], Sequence):
                kwargs[k] = [kwargs[k]]

        results = set()
        for attributes in self.files_attributes:
            if attribute_name in attributes.keys():
                add = True
                # If one of the required attribute is not ok, do not add
                for k in kwargs.keys():
                    if k not in attributes.keys() or (len(kwargs[k]) > 0 and attributes[k] not in kwargs[k]):
                        add = False
                        break
                if add:
                    results.add(attributes[attribute_name])
        return list(results)

    def get(self, **kwargs):
        """ Use the same query system that for list_all but list all matching files paths. """
        for k in kwargs.keys():
            if not isinstance(kwargs[k], Sequence):
                kwargs[k] = [kwargs[k]]

        results = []
        for path, attributes in zip(self.files, self.files_attributes):
            for k in kwargs.keys():
                add = True
                for k in kwargs.keys():
                    if k not in attributes.keys() or (len(kwargs[k]) > 0 and attributes[k] not in kwargs[k]):
                        add = False
                        break
                if add:
                    results.append(path)
                    break
        return results

    def get_from_template(self, template, **kwargs):
        """ Search files by parsing a template 

            Example
            ========
            >>>> graph = db.get_from_template("*/[subject]/t1mr1/*/*/folds/3.3/[session]/[hemi][session]_[subject].arg",
                                              subject=["sub-01", "sub-05"], session="session_manual", hemi="L")
        """

        file_paths = glob(extend_templates(
            op.join(self.path, template), default_value="*", **kwargs))

        results = []
        for fpath in file_paths:
            if op.isfile(fpath):
                results.append(fpath)
        return results
