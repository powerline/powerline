# vim:fileencoding=utf-8:noet

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
		super(VimPowerline, self).__init__('vim')

	def add_local_theme(self, key, config):
		'''Add local themes at runtime (during vim session).

		:param str key:
			Matcher name (in format ``{matcher_module}.{module_attribute}`` or 
			``{module_attribute}`` if ``{matcher_module}`` is 
			``powerline.matchers.vim``). Function pointed by 
			``{module_attribute}`` should be hashable and accept a dictionary 
			with information about current buffer and return boolean value 
			indicating whether current window matched conditions. See also 
			:ref:`local_themes key description <config-ext-local_themes>`.

		:param dict config:
			:ref:`Theme <config-themes>` dictionary.

		:return:
			``True`` if theme was added successfully and ``False`` if theme with 
			the same matcher already exists.
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
		return _override_from(super(VimPowerline, self).load_theme_config(name),
						'g:powerline_theme_overrides__' + name)

	def get_local_themes(self, local_themes):
		if not local_themes:
			return {}

		self.get_matcher = gen_matcher_getter(self.ext, self.import_paths)
		return dict(((self.get_matcher(key), {'config': self.load_theme_config(val)})
					for key, val in local_themes.items()))

	def get_config_paths(self):
		if vim_exists('g:powerline_config_path'):
			return [vim.eval('g:powerline_config_path')]
		else:
			return super(VimPowerline, self).get_config_paths()

	@staticmethod
	def get_segment_info():
		return {}
