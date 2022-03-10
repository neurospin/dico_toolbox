from builtins import ValueError, isinstance
from multiprocessing.sharedctypes import Value
import os
from random import random
import tempfile
from types import SimpleNamespace
import numpy
import logging
from ..convert import bucket_numpy_to_bucketMap_aims, ndarray_to_aims_volume
from ..wrappers import PyMesh
import anatomist.api as anatomist
from PIL import Image
from itertools import cycle

log = logging.getLogger(__name__)

os.environ["QT_API"] = "pyqt5"

message_lines = ["NOTES for jupyter users:"
                 "- You might need to set '%gui qt' in a cell of your notebook."
                 "- To hide anatomist logs, use the '%%capture' magic command at the beginning of the cell"]


def random_rgb_dict():
    """return a dictionnary with keys 'r', 'g' and 'b' and random float values in [0,1]"""
    v = numpy.random.randint(100, size=3)/100
    return dict(zip('rgb', v))


class Anatomist():
    _anatomist_instance = None
    default_colors_list = [[0.31, 1.19, 1.80],[2.55, 1.27, 0.14],[0.44, 1.6, 0.44],
                           [2.14, 0.39, 0.40],[1.48, 1.03, 1.89],[1.4, 0.86, 0.75],
                           [2.27, 1.19, 1.94],[1.27, 1.27, 1.27],[1.88, 1.89, 0.34],
                           [0.23, 1.9, 2.07]]
    

    def __init__(self):
        log.warning("\n".join(message_lines))

        # lazy creation of an anatomist instance
        if Anatomist._anatomist_instance is None:
            Anatomist._anatomist_instance = anatomist.Anatomist()

        self._instance = Anatomist._anatomist_instance
        self.windows = {}
        self.objects = {}
        self.anatomist_objects = {}
        self.blocks = {}
        
        self._default_colors_cycle = cycle([])
        self.reset_color_cycle()

        self.config = SimpleNamespace(
            new_window_view_quaternion=[0.55, -0.15, -0.15, 0.8],
            new_window_position=(0, 0),
            new_window_size=(500, 500)
        )
        
    def reset_color_cycle(self):
        self._default_colors_cycle = cycle(Anatomist.default_colors_list)

    def new_window(self, name, window_type, size=None, pos=None, camera_kwargs={}, **kwargs):
        if size is None:
            size = self.config.new_window_size
        if pos is None:
            pos = self.config.new_window_position

        kwargs['geometry'] = pos+size

        w = self._instance.createWindow(window_type, **kwargs)
        self.windows[name] = w

        # set camera position
        view_quaternion = camera_kwargs.get(
            "view_quaternion", self.config.new_window_view_quaternion)
        w.camera(view_quaternion=view_quaternion)
        return w

    def new_window_block(self, name="DefaultBlock", columns=2, windows=("Axial", "Sagittal", "Coronal", "3D"), size=None, pos=None):
        """Create a new window block"""
        block = self._instance.createWindowsBlock(2)  # 2 columns
        wd = {wt: self.new_window(
            f"{name}_{wt}", window_type=wt, block=block, pos=pos, size=size) for wt in windows}
        self.windows.update(wd)
        block.windows = wd
        self.blocks[name] = block

    def new_window_3D(self, name="Default", size=None, pos=None):
        """Create a new window"""
        self.new_window(name, window_type="3D", size=size, pos=pos)

    def new_window_Sagittal(self, name="Default", size=None, pos=None):
        self.new_window(name, window_type="Sagittal", size=size, pos=pos)

    def new_window_Axial(self, name="Default", size=None, pos=None):
        self.new_window(name, window_type="Axial", size=size, pos=pos)

    def new_window_Coronal(self, name="Default", size=None, pos=None):
        self.new_window(name, window_type="Coronal", size=size, pos=pos)

    def get_window_names(self):
        return list(self.windows.keys())

    def close(self):
        self._instance.close()

    def _delete_object(self, anatomist_object):
        """Remove all references to an anatomist object"""
        try:
            anatomist_object.releaseAppRef()
            anatomist_object.releaseRef()
        except Exception:
            pass

    def _get_keys_of_first_argument_if_dict(self, args):
        objects_names = args
        if len(args) == 1 and type(args[0]) == dict:
            objects_names = list(args[0].keys())
        return objects_names

    def delete_objects(self, *object_names):
        """Delete the specified objects by name.
        The argument can be a dictionnary, in which case the keys will be used as names."""
        object_names = self._get_keys_of_first_argument_if_dict(object_names)
        for name in object_names:
            self.objects.pop(name)
            o = self.anatomist_objects.pop(name)
            self._delete_object(o)

    def delete_all_objects(self):
        """Delete all objects"""
        self.delete_objects(self.anatomist_objects)
        self.anatomist_objects = {}
        self.objects = {}

    def get_anatomist_instance(self):
        return self._instance

    def reload_objects(self):
        self._instance.reloadObjects(self._instance.getObjects())

    def rename_object(self, old_name, new_name):
        """Rename an object"""
        if old_name not in self.objects:
            raise ValueError(f"{old_name} is not an existing object")

        self.objects[new_name] = self.objects.pop(old_name)
        self.anatomist_objects[new_name] = self.anatomist_objects.pop(
            old_name)

        m = self.anatomist_objects[new_name]
        m.setName(new_name)
        m.setChanged()
        m.notifyObservers()

    def _add_objects(self, *objects, window_names=["Default"], auto_color=False):
        if len(objects) == 1 and type(objects[0]) == dict:
            # argument is a dictionnary
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
                self._delete_object(existing_obj)

            m = self._instance.toAObject(obj)
            m.setName(str(name))
            m.setChanged()
            m.notifyObservers()
            m.addInWindows([self.windows[window_name]
                           for window_name in window_names])
            
            self.objects[name] = obj
            self.anatomist_objects[name] = m
            
            if auto_color:
                self.set_next_default_color(name)

    def clear_window(self, window_name="Default"):
        a = self.get_anatomist_instance()
        a.removeObjects(a.getObjects(), self.windows[window_name])

    def clear_block(self, block_name="DefaultBlock"):
        a = self.get_anatomist_instance()
        for w in self.blocks[block_name].windows:
            a.removeObjects(a.getObjects(), w)

    def add_objects_to_window(self, *objects, window_name="Default", auto_color=False):
        """Add one or more (comma separated) AIMS objects to a window.

        If a single dictionnary is given argument, the objects are labeled according to the dictionnary keys

        Args:
            window_name (str, optional): the name of the window. Defaults to "Default".
        """
        self._add_objects(*objects, window_names=[window_name], auto_color=auto_color)

    def set_objects_color(self, *object_names, r=0, g=0, b=0, alpha=1):
        """Set the color of an existing object.
        The argument can be a dictionnary, in which case the keys will be used as names.
        """
        m = self._instance.Material(diffuse=[r, g, b, alpha])

        object_names = self._get_keys_of_first_argument_if_dict(object_names)

        for name in object_names:
            obj = self.anatomist_objects.get(name, None)
            if obj is None:
                raise ValueError(f"The object {name} does not exist")

            obj.setMaterial(m)
            
    def set_next_default_color(self, obj_name):
        """Set the next default color to the object"""
        rgb = self._get_next_default_colors()[0]
        self.set_objects_color(obj_name,**rgb)

    def add_objects_to_block(self, *objects, block_name="DefaultBlock"):
        window_names = self.blocks[block_name].windows
        self._add_objects(objects, window_names=window_names)
        
    def _get_next_default_colors(self, length=1):
        """return a list of rdb dictionnary containing the next color from the default list)"""
        return [dict(zip('rgb', next(self._default_colors_cycle))) for i in range(length)]

    def draw3D(self, *objects, auto_color=False):
        """Quickly draw the objects in a new 3D window.
        color_dict is an r,g,b,a dictionnary of values in [0,1].
        """
        win_name = "quick"
        try:
            self.add_objects_to_window(*objects, window_name=win_name, auto_color=auto_color)
        except Exception:
            self.new_window_3D(win_name)
            self.add_objects_to_window(*objects, window_name=win_name, auto_color=auto_color)

    def draw_block(self, *objects):
        """Draw the objects in a new window block"""
        block_name = "quick"
        self.new_window_block(name=block_name)
        self.add_objects_to_block(*objects, block_name=block_name)

    def color_random(self, *object_names):
        """Set random color to the specified objects, or to all objects if None is specified."""
        if len(object_names) == 0:
            object_names = self.anatomist_objects.keys()
        for name in object_names:
            colors = random_rgb_dict()
            self.set_objects_color(name, **colors)

    def snapshot(self, window_name='quick'):
        """Take a snapshot of the speficified window."""
        with tempfile.NamedTemporaryFile(suffix='_temp.jpg', prefix='pyanatomist_') as f:
            window = self.windows.get(window_name, None)
            if window is None:
                raise ValueError(f"Window name {window_name} is not valid")
            window.snapshot(f.name)
            img = numpy.asarray(Image.open(f.name))
            return img

    def get_quick_window_reference(self):
        return self.windows.get('quick', None)

    def clear_quick_window(self):
        self.clear_window('quick')

    def __call__(self, *objects, auto_color=True):
        self.draw3D(*objects, auto_color=auto_color)

    def __str__(self):
        return "Anatomist wrapper."
