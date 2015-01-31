# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import platform
import os

from powerline import Powerline
from powerline.lib.overrides import parse_override_var
from powerline.lib.dict import mergeargs, mergedicts


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

	def load_main_config(self):
		r = super(PDBPowerline, self).load_main_config()
		config_overrides = os.environ.get('POWERLINE_CONFIG_OVERRIDES')
		if config_overrides:
			mergedicts(r, mergeargs(parse_override_var(config_overrides)))
		return r

	def load_theme_config(self, name):
		r = super(PDBPowerline, self).load_theme_config(name)
		theme_overrides = os.environ.get('POWERLINE_THEME_OVERRIDES')
		if theme_overrides:
			theme_overrides_dict = mergeargs(parse_override_var(theme_overrides))
			if name in theme_overrides_dict:
				mergedicts(r, theme_overrides_dict[name])
		return r

	def get_config_paths(self):
		paths = [path for path in os.environ.get('POWERLINE_CONFIG_PATHS', '').split(':') if path]
		return paths or super(PDBPowerline, self).get_config_paths()

	if sys.version_info < (3,) and platform.python_implementation() == 'PyPy':
		get_encoding = staticmethod(lambda: 'ascii')
