# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

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
