
__all__ = ['Loader']

from .reader import *
from .scanner import *
from .parser import *
from .composer import *
from .constructor import *
from .resolver import *

class Loader(Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)

