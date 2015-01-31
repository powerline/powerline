# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import platform

from powerline.renderers.shell.readline import ReadlineRenderer
from powerline.renderer import Renderer


class PDBRenderer(ReadlineRenderer):
	'''PDB-specific powerline renderer
	'''
	pdb = None
	initial_stack_length = None

	def get_segment_info(self, segment_info, mode):
		r = self.segment_info.copy()
		r['pdb'] = self.pdb
		r['initial_stack_length'] = self.initial_stack_length
		r['curframe'] = self.pdb.curframe
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
		if self.initial_stack_length is None:
			self.initial_stack_length = len(self.pdb.stack) - 1
		return Renderer.render(self, **kwargs)

	if sys.version_info < (3,) and platform.python_implementation() == 'PyPy':
		def do_render(self, **kwargs):
			# Make sure that only ASCII characters survive
			ret = super(PDBRenderer, self).do_render(**kwargs)
			ret = ret.encode('ascii', 'replace')
			ret = ret.decode('ascii')
			return ret


renderer = PDBRenderer
