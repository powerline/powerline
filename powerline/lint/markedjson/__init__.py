
from .error import *

from .tokens import *
from .events import *
from .nodes import *

from .loader import *

__version__ = '3.10'

def load(stream, Loader=Loader):
    """
    Parse the first YAML document in a stream
    and produce the corresponding Python object.
    """
    loader = Loader(stream)
    try:
        r = loader.get_single_data()
        return r, loader.haserrors
    finally:
        loader.dispose()

