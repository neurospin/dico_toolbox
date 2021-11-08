import os
from soma import aims
from dico_toolbox.test_data import load_data


class paths:
    bucket_example = os.path.join(load_data(), "bucket.bck")


class _Data:
    # lazy data loader
    # Load the object only at first access, then return a reference to it
    def __init__(self):
        pass

    def __getattr__(self, name):
        val = aims.read(paths.__dict__.get(name, None))
        if val is None:
            raise AttributeError("Unavailable resource")
        self.__setattr__(name, val)
        return val


data = _Data()
