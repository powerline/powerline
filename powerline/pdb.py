# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import platform

from powerline import Powerline


class PDBPowerline(Powerline):
	'''PDB-specific powerline bindings
	'''
	def init(self, **kwargs):
		return super(PDBPowerline, self).init(
			ext='pdb',
			renderer_module='pdb',
			**kwargs
		)

	def do_setup(self, pdb):
		self.update_renderer()
		self.renderer.set_pdb(pdb)

	if sys.version_info < (3,) and platform.python_implementation() == 'PyPy':
		get_encoding = staticmethod(lambda: 'ascii')
