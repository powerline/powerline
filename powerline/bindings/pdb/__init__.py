# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.pdb import PDBPowerline
from powerline.lib.encoding import get_preferred_output_encoding


def use_powerline_prompt(cls):
	'''Decorator that installs powerline prompt to the class

	:param pdb.Pdb cls:
		Class that should be decorated.

	:return:
		``cls`` argument or a class derived from it. Latter is used to turn 
		old-style classes into new-style classes.
	'''
	encoding = get_preferred_output_encoding()

	@property
	def prompt(self):
		try:
			powerline = self.powerline
		except AttributeError:
			powerline = PDBPowerline()
			powerline.setup(self)
			self.powerline = powerline
		ret = powerline.render(side='left')
		if not isinstance(ret, str):
			# Python-2
			ret = ret.encode(encoding)
		return ret

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
