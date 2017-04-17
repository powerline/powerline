# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import pdb

from powerline.pdb import PDBPowerline
from powerline.lib.encoding import get_preferred_output_encoding
from powerline.lib.unicode import unicode


if sys.version_info < (3,):
	# XXX The below classes make code compatible with PDBpp which uses pyrepl
	#     which does not expect unicode or something above ASCII. They are 
	#     completely not needed if pdbpp is not used, but that’s not always the 
	#     case.
	class PowerlineRenderBytesResult(bytes):
		def __new__(cls, s, encoding=None):
			encoding = encoding or s.encoding
			if isinstance(s, PowerlineRenderResult):
				return s.encode(encoding)
			self = bytes.__new__(cls, s.encode(encoding) if isinstance(s, unicode) else s)
			self.encoding = encoding
			return self

		for meth in (
			'__contains__',
			'partition', 'rpartition',
			'split', 'rsplit',
			'count', 'join',
		):
			exec((
				'def {0}(self, *args):\n'
				'	if any((isinstance(arg, unicode) for arg in args)):\n'
				'		return self.__unicode__().{0}(*args)\n'
				'	else:\n'
				'		return bytes.{0}(self, *args)'
			).format(meth))

		for meth in (
			'find', 'rfind',
			'index', 'rindex',
		):
			exec((
				'def {0}(self, *args):\n'
				'	if any((isinstance(arg, unicode) for arg in args)):\n'
				'		args = [arg.encode(self.encoding) if isinstance(arg, unicode) else arg for arg in args]\n'
				'	return bytes.{0}(self, *args)'
			).format(meth))

		def __len__(self):
			return len(self.decode(self.encoding))

		def __getitem__(self, *args):
			return PowerlineRenderBytesResult(bytes.__getitem__(self, *args), encoding=self.encoding)

		def __getslice__(self, *args):
			return PowerlineRenderBytesResult(bytes.__getslice__(self, *args), encoding=self.encoding)

		@staticmethod
		def add(encoding, *args):
			if any((isinstance(arg, unicode) for arg in args)):
				return PowerlineRenderResult(''.join((
					arg
					if isinstance(arg, unicode)
					else arg.decode(encoding)
					for arg in args
				)), encoding)
			else:
				return PowerlineRenderBytesResult(b''.join(args), encoding=encoding)

		def __add__(self, other):
			return self.add(self.encoding, self, other)

		def __radd__(self, other):
			return self.add(self.encoding, other, self)

		def __unicode__(self):
			return PowerlineRenderResult(self)

	class PowerlineRenderResult(unicode):
		def __new__(cls, s, encoding=None):
			encoding = (
				encoding
				or getattr(s, 'encoding', None)
				or get_preferred_output_encoding()
			)
			if isinstance(s, unicode):
				self = unicode.__new__(cls, s)
			else:
				self = unicode.__new__(cls, s, encoding, 'replace')
			self.encoding = encoding
			return self

		def __str__(self):
			return PowerlineRenderBytesResult(self)

		def __getitem__(self, *args):
			return PowerlineRenderResult(unicode.__getitem__(self, *args))

		def __getslice__(self, *args):
			return PowerlineRenderResult(unicode.__getslice__(self, *args))

		@staticmethod
		def add(encoding, *args):
			return PowerlineRenderResult(''.join((
				arg
				if isinstance(arg, unicode)
				else arg.decode(encoding)
				for arg in args
			)), encoding)

		def __add__(self, other):
			return self.add(self.encoding, self, other)

		def __radd__(self, other):
			return self.add(self.encoding, other, self)

		def encode(self, *args, **kwargs):
			return PowerlineRenderBytesResult(unicode.encode(self, *args, **kwargs), args[0])
else:
	PowerlineRenderResult = str


def use_powerline_prompt(cls):
	'''Decorator that installs powerline prompt to the class

	:param pdb.Pdb cls:
		Class that should be decorated.

	:return:
		``cls`` argument or a class derived from it. Latter is used to turn 
		old-style classes into new-style classes.
	'''
	@property
	def prompt(self):
		try:
			powerline = self.powerline
		except AttributeError:
			powerline = PDBPowerline()
			powerline.setup(self)
			self.powerline = powerline
		return PowerlineRenderResult(powerline.render(side='left'))

	@prompt.setter
	def prompt(self, _):
		pass

	@prompt.deleter
	def prompt(self):
		pass

	if not hasattr(cls, '__class__'):
		# Old-style class: make it new-style or @property will not work.
		old_cls = cls

		class cls(cls, object):
			__module__ = cls.__module__
			__doc__ = cls.__doc__

		cls.__name__ = old_cls.__name__

	cls.prompt = prompt

	return cls


def main():
	'''Run module as a script

	Uses :py:func:`pdb.main` function directly, but prior to that it mocks 
	:py:class:`pdb.Pdb` class with powerline-specific class instance.
	'''
	orig_pdb = pdb.Pdb

	@use_powerline_prompt
	class Pdb(pdb.Pdb, object):
		def __init__(self):
			orig_pdb.__init__(self)

	pdb.Pdb = Pdb

	return pdb.main()
