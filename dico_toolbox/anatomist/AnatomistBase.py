from argparse import ArgumentError
from multiprocessing.sharedctypes import Value
import os
import logging
import anatomist.api as anatomist


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

    def set_object_color(self, object_name, r=0, g=0, b=0, alpha=1):
        """Set the color of an existing object"""
        obj = self.anatomist_objects.get(object_name, None)
        if obj is None:
            raise ArgumentError(f"The object {object_name} does not exist")
        m = self._instance.Material(diffuse=[r, g, b, alpha])
        obj.setMaterial(m)

    def add_objects_to_block(self, *objects, block_name="DefaultBlock"):
        window_names = self.blocks[block_name].windows
        self._add_objects(objects, window_names=window_names)

    def draw3D(self, *objects):
        """Quickly draw the objects in a new 3D window"""
        win_name = "quick"
        self.new_window_3D(name=win_name)
        self.add_objects_to_window(*objects, window_name=win_name)

    def draw_block(self, *objects):
        """Draw the objects in a new window block"""
        block_name = "quick"
        self.new_window_block(name=block_name)
        self.add_objects_to_block(*objects, block_name=block_name)

    def __call__(self, *objects):
        self.draw3D(*objects)
