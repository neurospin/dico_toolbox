# [treesource] access Brainvisa databases
import os.path as op
from os import listdir
import os
from typing import Union
from collections.abc import Sequence
from glob import glob
from warnings import warn


def extend_templates(templates, default_value=None, start_tag="[", end_tag="]", **kwargs):
    """ """
    if not isinstance(templates, (list, tuple)):
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

        for key in unused_keys:
            for it, template in enumerate(templates):
                templates[it] = template.replace(
                    start_tag + key + end_tag, default_value)

    # Then list all possibilities
    for k in used_keys:
        tag = start_tag + k + end_tag
        if not isinstance(kwargs[k], (list, tuple)):
            kwargs[k] = [kwargs[k]]
        new_templates = []
        for template in templates:
            if tag in template:
                for val in kwargs[k]:
                    new_templates.append(template.replace(
                        start_tag + k + end_tag, val))
        templates = new_templates

    return templates


FILES_COUNT_WARNING = 500


class FileDatabase:
    def __init__(self, path: str, directory_levels=[], templates: dict = {},
                 allowed_extensions="*", forbidden_extensions=[]):
        if not op.isdir(path):
            raise IOError(
                "The database path must point to an existing directory.")
        self.path = path
        self.allowed_extensions = allowed_extensions
        self.forbidden_extensions = forbidden_extensions

        self.templates = templates
        self.directory_levels = directory_levels

        self.files = []
        self.files_attributes = []
        self.attributes = []

    def is_valid_path(self, path: str):
        if not op.isfile(path):
            return False
        ext = op.splitext(path)[1][1:]

        if self.allowed_extensions == "*":
            return ext not in self.forbidden_extensions

        return ext in self.allowed_extensions and ext not in self.forbidden_extensions

    # TODO: add possibility to specify integer values in templates (+ formating)
    def get_from_template(self, template, **kwargs):
        """ Search files by parsing a template

            Example
            ========
            >>>> graph = db.get_from_template("*/[subject]/t1mr1/*/*/folds/3.3/[session]/[hemi][session]_[subject].arg",
                                                subject=["sub-01", "sub-05"], session="session_manual", hemi="L")
        """
        if template in self.templates:
            template = self.templates[template]

        paths = extend_templates(
            op.join(self.path, template), default_value="*", **kwargs)

        file_paths = []
        for p in paths:
            file_paths.extend(glob(p))

        results = []
        for fpath in file_paths:
            if self.is_valid_path(fpath):
                results.append(fpath)
        return results

    def generate_from_templates(self, templates, start_tag="[", end_tag="]", makedirs=False, **kwargs):
        """ Usefull to generate new files paths """
        if not isinstance(templates, (tuple, list)):
            templates = [templates]

        for t in range(len(templates)):
            if templates[t] in self.templates:
                templates[t] = op.join(self.path, self.templates[templates[t]])

        for k in kwargs.keys():
            tag = start_tag + k + end_tag
            if not isinstance(kwargs[k], (list, tuple)):
                kwargs[k] = [kwargs[k]]
            new_templates = []
            for template in templates:
                if tag in template:
                    for val in kwargs[k]:
                        new_templates.append(template.replace(
                            start_tag + k + end_tag, val))
            templates = new_templates

        if makedirs:
            for templ in templates:
                d, _ = op.split(templ)
                os.makedirs(d, exist_ok=True)
        return templates

    def generate_from_template(self, template, start_tag="[", end_tag="]", makedirs=False, **kwargs):
        return self.generate_from_templates(template, start_tag, end_tag, makedirs, **kwargs)[0]

    def _add_file(self, path, **kwargs):
        if not self.is_valid_path(path) or path in self.files:
            return

        if len(self.files) == FILES_COUNT_WARNING:
            warn("Database seems to be large. You might consider to use path template "
                 "instead of use methods that require to scan all the database")

        ext = op.splitext(path)[1][1:]
        # if ext == "gz":
        #     ext = '.'.join(op.split(path)[1].split('.')[-2:])
        kwargs['extension'] = ext

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

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

    def scan(self):
        self.files = []
        self.files_attributes = []
        self.attributes = {}

        # Expect output as:
        # db/center/subject/acqusition/analysis/segmentation
        # db/center/subject/acqusition/analysis/folds
        # TODO: add unscan _attributes?
        # FIXME: analysis cannot be listed as we do not go into the foldeer to list files
        self.unscan_paths = self._scan_subdirectories(
            self.path, self.directory_levels)

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
        if len(self.files) == 0:
            self.scan()

        for k in kwargs.keys():
            if not isinstance(kwargs[k], (list, tuple)):
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
        if len(self.files) == 0:
            self.scan()

        for k in kwargs.keys():
            if not isinstance(kwargs[k], (list, tuple)):
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

    def get_attribute_of(self, path: str) -> dict():
        # TODO: implement this
        raise NotImplementedError()


def infer_file_type(fpath, attributes):
    """ Infer Axon file type from the path and attributes """
    # TODO: list file type somewhere
    if attributes['extension'] == '.arg':
        return "graph"
    elif attributes['extension'] == '.his':
        return "histogram"
    return "unkown"


BV_TEMPLATES = {
    "morpgologist_graph": "[center]/[subject]/t1mri/[acquisition]/[analysis]/folds/[version]/[hemi][subject].arg",
    "morphologist_labelled_graph": "[center]/[subject]/t1mri/[acquisition]/[analysis]/folds/[version]/[session]/[hemi][subject]_[session].arg",
    "morphologist_mesh": "[center]/[subject]/t1mri/[acquisition]/[analysis]/segmentation/mesh/[subject]_[hemi][type].[extension]",
    "morphologist_segmentation": "[center]/[subject]/t1mri/[acquisition]/[analysis]/segmentation/[hemi][type]_[subject].[extension]",
}


class BVDatabase(FileDatabase):
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

    def __init__(self, path: str):
        super().__init__(
            path,
            templates=BV_TEMPLATES,
            directory_levels=["center", "subject",
                              "modality", "acquisition", "analysis"],
            forbidden_extensions=['minf']
        )

    def _add_file(self, path, **kwargs):
        super()._add_file(path, **kwargs)
        # TODO: use .minf to get more attributes?
        # self.files_attributes[-1]['type'] = infer_file_type(path, kwargs)

    def _scan_morphologist_analyses(self, modality="t1mri"):
        # Look for Morphologist outputs
        for center in self.list_all('center'):
            for sub in self.list_all('subject', center=center, modality=modality):
                for acq in self.list_all('acquisition', center=center, subject=sub, modality=modality):
                    for ana in listdir(op.join(self.path, center, sub, modality, acq)):
                        # for ana in self.list_all('subject', center=center, subject=sub, modality="t1mri", acquisition=acq):
                        ana_path = op.join(
                            self.path, center, sub, modality, acq, ana)
                        if not op.isdir(ana_path):
                            continue
                        seg_path = op.join(ana_path, "segmentation")
                        mesh_path = op.join(seg_path, "mesh")
                        fold_path = op.join(ana_path, "folds")

                        for f in listdir(ana_path):
                            fpath = op.join(ana_path, f)
                            if op.isfile(fpath):
                                self._add_file(
                                    fpath, center=center, subject=sub, modality=modality,
                                    acquisition=acq, analysis=ana)

                        # Segmented volumes
                        if op.isdir(seg_path):
                            for f in listdir(seg_path):
                                fpath = op.join(seg_path, f)
                                if op.isfile(fpath):
                                    # [hemi][seg_type]_[subject].[extension]
                                    fname, _ = op.splitext(f)
                                    seg_type = fname[:-len(sub)-1] if len(
                                        fname) > len(sub) else None
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
                            # Meshes
                            if op.isdir(mesh_path):
                                for f in listdir(mesh_path):
                                    fpath = op.join(mesh_path, f)
                                    if op.isfile(fpath):
                                        # [subject]_[hemi][seg_type].[extension]
                                        fname, _ = op.splitext(f)
                                        mesh_type = fname[len(
                                            sub)+1:] if len(fname) > len(sub) else None
                                        hemi = mesh_type[0] if mesh_type else None

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
                        # Graphs
                        if op.isdir(fold_path):
                            for version in listdir(fold_path):
                                fold_subpath = op.join(fold_path, version)

                                for f in listdir(fold_subpath):
                                    fpath = op.join(fold_subpath, f)
                                    if op.isfile(fpath):
                                        # [hemi][subject]_[seg_type].[extension]
                                        fname, _ = op.splitext(f)
                                        seg_type = fname[len(
                                            sub)+1:] if len(fname) > len(sub) else None
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
                                        session_path = op.join(
                                            fold_subpath, session)
                                        for f in listdir(session_path):
                                            fpath = op.join(session_path, f)
                                            if op.isfile(fpath) and f[-4:] == ".arg":
                                                # [hemi][subject]_[session].arg
                                                fname, _ = op.splitext(f)
                                                hemi = fname[0]
                                                if hemi in ['L', 'R']:
                                                    hemi = 'left' if hemi == 'L' else 'right'
                                                    self._add_file(fpath, center=center, subject=sub, modality=modality,
                                                                   acquisition=acq, analysis=ana, hemisphere=hemi,
                                                                   graph_version=version, graph_session=session)

    def scan(self):
        super().scan()
        self._scan_morphologist_analyses()
