import os
import logging
import anatomist.api as anatomist


log = logging.getLogger(__name__)

os.environ["QT_API"] = "pyqt5"

message_lines = ["NOTES for jupyter users:"
                 "Remember to set '%gui qt' in a cell of your notebook"
                 "To hide anatomist logs, use the '%%capture' magic command at the beginning of the cell"]


class Anatomist():
    info_displayed = False
    instance = None
    windows = {}

    def __init__(self):
        log.warning("/n".join(message_lines))
        self.instance = anatomist.Anatomist()

    def new_window_3D(self, name="Default"):
        w = self.instance.createWindow("3D", geometry=[1200, 350, 500, 500])
        self.windows[name] = w

    def close(self):
        self.instance.close()

    def add_objects(self, objects, window_name="Default"):
        if type(objects) == dict:
            pass
        elif type(objects) in [list, tuple]:
            # list to dict
            objects = {str(n): obj for n, obj in enumerate(object)}

        for name, obj in objects.items():
            m = self.instance.toAObject(obj)
            m.name = name
            m.addInWindows(self.windows[window_name])
