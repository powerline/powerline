# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from pkgutil import extend_path
from types import MethodType


__path__ = extend_path(__path__, __name__)


class Segment(object):
	'''Base class for any segment that is not a function

	Required for powerline.lint.inspect to work properly: it defines methods for 
	omitting existing or adding new arguments.

	.. note::
		Until python-3.4 ``inspect.getargspec`` does not support querying 
		callable classes for arguments of their ``__call__`` method, requiring 
		to use this method directly (i.e. before 3.4 you should write 
		``getargspec(obj.__call__)`` in place of ``getargspec(obj)``).
	'''
	if sys.version_info < (3, 4):
		def argspecobjs(self):
			yield '__call__', self.__call__
	else:
		def argspecobjs(self):
			yield '__call__', self

	argspecobjs.__doc__ = (
		'''Return a list of valid arguments for inspect.getargspec

		Used to determine function arguments.
		'''
	)

	def omitted_args(self, name, method):
		'''List arguments which should be omitted

		Returns a tuple with indexes of omitted arguments.

		.. note::``segment_info``, ``create_watcher`` and ``pl`` will be omitted 
			regardless of the below return (for ``segment_info`` and 
			``create_watcher``: only if object was marked to require segment 
			info or filesystem watcher).
		'''
		if isinstance(self.__call__, MethodType):
			return (0,)
		else:
			return ()

	@staticmethod
	def additional_args():
		'''Returns a list of (additional argument name[, default value]) tuples.
		'''
		return ()


def with_docstring(instance, doc):
	instance.__doc__ = doc
	return instance
