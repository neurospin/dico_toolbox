from builtins import ValueError, isinstance
from argparse import ArgumentError
from multiprocessing.sharedctypes import Value
import os
import tempfile
import numpy
import logging
from ..convert import bucket_numpy_to_bucketMap_aims, ndarray_to_aims_volume
from ..wrappers import PyMesh
import anatomist.api as anatomist
from PIL import Image


log = logging.getLogger(__name__)

os.environ["QT_API"] = "pyqt5"

message_lines = ["NOTES for jupyter users:"
                 "- You might need to set '%gui qt' in a cell of your notebook."
                 "- To hide anatomist logs, use the '%%capture' magic command at the beginning of the cell"]


class Anatomist():
    info_displayed = False
    _instance = None
    windows = {}
    objects = {}
    anatomist_objects = {}
    blocks = {}

    def __init__(self):
        log.warning("\n".join(message_lines))
        self._instance = anatomist.Anatomist()

    def _new_window(self, name, window_type, **kwargs):
        w = self._instance.createWindow(window_type, **kwargs)
        self.windows[name] = w
        return w

    def new_window_block(self, name="DefaultBlock", columns=2, windows=("Axial", "Sagittal", "Coronal", "3D"), size=(500, 500), pos=(0, 0)):
        """Create a new window block"""
        block = self._instance.createWindowsBlock(2)  # 2 columns
        wd = {wt: self._new_window(
            f"{name}_{wt}", window_type=wt, block=block, geometry=pos + size) for wt in windows}
        self.windows.update(wd)
        block.windows = wd
        self.blocks[name] = block

    def new_window_3D(self, name="Default", size=(500, 500), pos=(0, 0)):
        """Create a new window"""
        self._new_window(name, window_type="3D", geometry=pos + size)

    def new_window_Sagittal(self, name="Default", size=(500, 500), pos=(0, 0)):
        self._new_window(name, window_type="Sagittal", geometry=pos + size)

    def new_window_Axial(self, name="Default", size=(500, 500), pos=(0, 0)):
        self._new_window(name, window_type="Axial", geometry=pos + size)

    def new_window_Coronal(self, name="Default", size=(500, 500), pos=(0, 0)):
        self._new_window(name, window_type="Coronal", geometry=pos + size)

    def get_window_names(self):
        return list(self.windows.keys())

    def close(self):
        self._instance.close()

    def _delete_object(self, anatomist_object):
        try:
            anatomist_object.releaseAppRef()
            anatomist_object.releaseRef()
        except Exception:
            pass

    def delete_objects(self, *object_names):
        for name in object_names:
            self.objects.pop(name)
            o = self.anatomist_objects.pop(name)
            self._delete_object(o)

    def get_anatomist_instance(self):
        return self._instance

    def reload_objects(self):
        self._instance.reloadObjects(self._instance.getObjects())

    def rename_object(self, old_name, new_name):
        """Rename an object"""
        if old_name not in self.objects:
            raise ArgumentError(f"{old_name} is not an existing object")

        self.objects[new_name] = self.objects.pop(old_name)
        self.anatomist_objects[new_name] = self.anatomist_objects.pop(
            old_name)

        m = self.anatomist_objects[new_name]
        m.setName(new_name)
        m.setChanged()
        m.notifyObservers()

    def _add_objects(self, objects, window_names=["Default"]):
        if len(objects) == 1 and type(objects[0]) == dict:
            objects = objects[0]
        elif type(objects) in [list, tuple]:
            # list to dict
            objects = {n: obj for n, obj in enumerate(objects)}

        for name, obj in objects.items():

            if isinstance(obj, numpy.ndarray):
                # Object is a NUMPY arrays
                if len(obj.shape) == 2 and obj.shape[1] == 3:
                    # object is a point cloud
                    obj = bucket_numpy_to_bucketMap_aims(obj)
                elif len(obj.shape) == 3:
                    # object is a volume
                    obj = ndarray_to_aims_volume(obj)
                else:
                    raise ValueError(
                        f"object {name} is an unconvertible numpy array.")

            if isinstance(obj, PyMesh):
                # obj is a PyMesh
                obj = obj.to_aims_mesh()

            # remove existing objects from anatomist
            existing_obj = self.anatomist_objects.get(name, None)
            if existing_obj is not None:
                # self._instance.deleteObjects([existing_obj])
                self._delete_object(existing_obj)

            m = self._instance.toAObject(obj)
            m.setName(str(name))
            m.setChanged()
            m.notifyObservers()
            m.addInWindows([self.windows[window_name]
                           for window_name in window_names])
            self.objects[name] = obj
            self.anatomist_objects[name] = m

    def clear_window(self, window_name="Default"):
        a = self.get_anatomist_instance()
        a.removeObjects(a.getObjects(), self.windows[window_name])

    def clear_block(self, block_name="DefaultBlock"):
        a = self.get_anatomist_instance()
        for w in self.blocks[block_name].windows:
            a.removeObjects(a.getObjects(), w)

    def add_objects_to_window(self, *objects, window_name="Default"):
        """Add one or more (comma separated) AIMS objects to a window.

        If a single dictionnary is given argument, the objects are labeled according to the dictionnary keys

        Args:
            window_name (str, optional): the name of the window. Defaults to "Default".
        """
        self._add_objects(objects, window_names=[window_name])

    def set_objects_color(self, *object_names, r=0, g=0, b=0, alpha=1):
        """Set the color of an existing object"""
        m = self._instance.Material(diffuse=[r, g, b, alpha])

        if isinstance(object_names[0], dict):
            object_names = object_names[0].keys()

        for name in object_names:
            obj = self.anatomist_objects.get(name, None)
            if obj is None:
                raise ArgumentError(f"The object {name} does not exist")

            obj.setMaterial(m)

    def add_objects_to_block(self, *objects, block_name="DefaultBlock"):
        window_names = self.blocks[block_name].windows
        self._add_objects(objects, window_names=window_names)

    def draw3D(self, *objects):
        """Quickly draw the objects in a new 3D window"""
        win_name = "quick"
        try:
            self.add_objects_to_window(*objects, window_name=win_name)
        except Exception:
            self.new_window_3D(win_name)
            self.add_objects_to_window(*objects, window_name=win_name)

    def draw_block(self, *objects):
        """Draw the objects in a new window block"""
        block_name = "quick"
        self.new_window_block(name=block_name)
        self.add_objects_to_block(*objects, block_name=block_name)

    def color_random(self, *object_names):
        """Set random color to the specified objects, ore to all objects if None is specified."""
        if len(object_names) == 0:
            object_names = self.anatomist_objects.keys()
        for name in object_names:
            r, g, b = numpy.random.randint(100, size=3)/100
            self.set_objects_color(name, r=r, g=g, b=b)

    def snapshot(self, window_name='quick'):
        """Take a snapshot of the speficified window."""
        with tempfile.NamedTemporaryFile(suffix='_temp.jpg', prefix='pyanatomist_') as f:
            window = self.windows.get(window_name, None)
            if window is None:
                raise ArgumentError(f"Window name {window_name} is not valid")
            window.snapshot(f.name)
            img = numpy.asarray(Image.open(f.name))
            return img

    def clear_quick_window(self):
        self.new_window_3D('quick')

    def __call__(self, *objects):
        self.draw3D(*objects)

    def __str__(self):
        return "Anatomist wrapper."
