__all__ = ['Loader']

from .reader import Reader
from .scanner import Scanner
from .parser import Parser
from .composer import Composer
from .constructor import Constructor
from .resolver import Resolver
from .error import echoerr


class Loader(Reader, Scanner, Parser, Composer, Constructor, Resolver):
	def __init__(self, stream):
		Reader.__init__(self, stream)
		Scanner.__init__(self)
		Parser.__init__(self)
		Composer.__init__(self)
		Constructor.__init__(self)
		Resolver.__init__(self)
		self.haserrors = False

	def echoerr(self, *args, **kwargs):
		echoerr(*args, **kwargs)
		self.haserrors = True
