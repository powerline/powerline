# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lint.markedjson.reader import Reader
from powerline.lint.markedjson.scanner import Scanner
from powerline.lint.markedjson.parser import Parser
from powerline.lint.markedjson.composer import Composer
from powerline.lint.markedjson.constructor import Constructor
from powerline.lint.markedjson.resolver import Resolver
from powerline.lint.markedjson.error import echoerr


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
