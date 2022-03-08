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
    _anatomist_objects = {}
    blocks = {}

    def __init__(self):
        log.warning("\n".join(message_lines))
        self._instance = anatomist.Anatomist()

    def _new_window(self, name, window_type, **kwargs):
        w = self._instance.createWindow(window_type, **kwargs)
        self.windows[name] = w
        return w

    def new_window_block(self, name="DefaultBlock", columns=2, windows=("Axial", "Sagittal", "Coronal", "3D")):
        """Create a new window block"""
        block = self._instance.createWindowsBlock(2)  # 2 columns
        wd = {wt: self._new_window(
            f"{name}_{wt}", window_type=wt, block=block) for wt in windows}
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

    def get_anatomist_objects(self):
        """Get the objects as Aims objects"""
        return self._anatomist_objects

    def reload_objects(self):
        self._instance.reloadObjects(self._instance.getObjects())

    def _add_objects(self, objects, window_names=["Default"]):
        if len(objects) == 1 and type(objects[0]) == dict:
            objects = objects[0]
        elif type(objects) in [list, tuple]:
            # list to dict
            objects = {n: obj for n, obj in enumerate(objects)}

        for name, obj in objects.items():
            m = self._instance.toAObject(obj)
            # m.name = name
            m.addInWindows([self.windows[window_name]
                           for window_name in window_names])
            self.objects[name] = obj
            self._anatomist_objects[name] = m

    def clear_window(self, window_name="Default"):
        a = self.get_anatomist_instance()
        a.removeObjects(a.getObjects(), self.windows[window_name])

    def clear_block(self, block_name="DefaultBlock"):
        a = self.get_anatomist_instance()
        for w in self.blocks[block_name].windows:
            a.removeObjects(a.getObjects(), w)

    def add_objects_to_window(self, *objects, window_name="Default"):
        """Add one or more (comma separated) AIMS objects to a window.

        Args:
            window_name (str, optional): the name of the window. Defaults to "Default".
        """
        self._add_objects(objects, window_names=[window_name])

    def add_objects_to_block(self, *objects, block_name="DefaultBlock"):
        window_names = self.blocks[block_name].windows
        self._add_objects(objects, window_names=window_names)
