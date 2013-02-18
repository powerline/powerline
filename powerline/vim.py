# -*- coding: utf-8 -*-

from __future__ import absolute_import

from powerline.bindings.vim import vim_get_func
from powerline import Powerline
from powerline.lib import mergedicts
from powerline.matcher import gen_matcher_getter
import vim


vim_exists = vim_get_func('exists', rettype=int)

def _override_from(config, override_varname):
	if vim_exists(override_varname):
		# FIXME vim.eval has problem with numeric types, vim.bindeval may be 
		# absent (and requires converting values to python built-in types), 
		# vim.eval with typed call like the one I implemented in frawor is slow. 
		# Maybe eval(vime.eval('string({0})'.format(override_varname)))?
		overrides = vim.eval(override_varname)
		mergedicts(config, overrides)
	return config


class VimPowerline(Powerline):
	def __init__(self):
		return super(VimPowerline, self).__init__('vim')

	def add_local_theme(self, key, config):
		'''Add local themes at runtime (during vim session).

		Accepts key as first argument (same as keys in config.json:
		ext/*/local_themes) and configuration dictionary as the second (has
		format identical to themes/*/*.json)

		Returns True if theme was added successfully and False if theme with
		the same matcher already exists
		'''
		key = self.get_matcher(key)
		try:
			self.renderer.add_local_theme(key, {'config': config})
		except KeyError:
			return False
		else:
			return True

	def load_main_config(self):
		return _override_from(super(VimPowerline, self).load_main_config(), 'g:powerline_config_overrides')

	def load_theme_config(self, name):
		# Note: themes with non-[a-zA-Z0-9_] names are impossible to override 
		# (though as far as I know exists() won’t throw). Won’t fix, use proper 
		# theme names.
		return _override_from(super(VimPowerline, self).load_theme_config(name), 'g:powerline_theme_overrides__'+name)

	def get_local_themes(self, local_themes):
		self.get_matcher = gen_matcher_getter(self.ext, self.import_paths)
		local_themes = {}
		for key, local_theme_name in local_themes.items():
			key = self.get_matcher(key)
			local_themes[key] = {'config': self.load_theme_config(ext, local_theme_name)}
		return local_themes

	@staticmethod
	def get_segment_info():
		return {}
