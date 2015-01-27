# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell.readline import ReadlineRenderer
from powerline.renderer import Renderer


class PDBRenderer(ReadlineRenderer):
	'''PDB-specific powerline renderer
	'''
	pdb = None

	def get_segment_info(self, segment_info, mode):
		r = self.segment_info.copy()
		r['pdb'] = self.pdb
		return r

	def set_pdb(self, pdb):
		'''Record currently used :py:class:`pdb.Pdb` instance

		Must be called before first calling :py:meth:`render` method.

		:param pdb.Pdb pdb:
			Used :py:class:`pdb.Pdb` instance. This instance will later be used 
			by :py:meth:`get_segment_info` for patching :ref:`segment_info 
			<dev-segments-info>` dictionary.
		'''
		self.pdb = pdb

	def render(self, **kwargs):
		return Renderer.render(self, **kwargs)


renderer = PDBRenderer
