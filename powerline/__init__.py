# vim:fileencoding=UTF-8:ts=4:sw=4:sta:noet:sts=4:fdm=marker:ai

from __future__ import absolute_import
import json
import os
import sys
import copy

from powerline.colorscheme import Colorscheme
from powerline.lib import underscore_to_camelcase

class ConfigCache(object):

	def __init__(self):
		self.cache = {}

	def __call__(self, search_paths, config_file):
		config_file += '.json'
		for path in search_paths:
			config_file_path = os.path.join(path, config_file)
			try:
				st = os.stat(config_file_path)
			except EnvironmentError:
				continue
			mtime, parsed = self.cache.get(config_file_path, (None, None))
			if mtime is None or mtime < st.st_mtime:
				with open(config_file_path, 'rb') as f:
					parsed = json.loads(f.read())
				self.cache[config_file_path] = (st.st_mtime, parsed)
			# We return a copy because other code might modify the returned
			# object.
			return copy.deepcopy(parsed)

		raise IOError('Config file not found in search path: {0}'.format(config_file))

load_json_config = ConfigCache()

class Powerline(object):
	'''Main powerline class, entrance point for all powerline uses. Sets
	powerline up and loads the configuration.

	:param str ext:
		extension used. Determines where configuration files will
		searched and what renderer module will be used. Affected: used ``ext``
		dictionary from :file:`powerline/config.json`, location of themes and
		colorschemes, render module (``powerline.renders.{ext}``).
	:param str renderer_module:
		Overrides renderer module (defaults to ``ext``). Should be the name of
		the package imported like this: ``powerline.renders.{render_module}``.
	'''

	def __init__(self, ext, renderer_module=None):
		self.config_paths = self.get_config_paths()

		# Load main config file
		config = self.load_main_config()
		common_config = config['common']
		ext_config = config['ext'][ext]
		self.ext = ext

		# Load and initialize colorscheme
		colorscheme_config = self.load_colorscheme_config(ext_config['colorscheme'])
		colors_config = self.load_colors_config()
		colorscheme = Colorscheme(colorscheme_config, colors_config)

		# Load and initialize extension theme
		theme_config = self.load_theme_config(ext_config.get('theme', 'default'))
		common_config['paths'] = [os.path.expanduser(path) for path in common_config.get('paths', [])]
		self.import_paths = common_config['paths']
		theme_kwargs = {
			'ext': ext,
			'common_config': common_config,
			'segment_info': self.get_segment_info(),
			}
		local_themes = self.get_local_themes(ext_config.get('local_themes', {}))

		# Load and initialize extension renderer
		renderer_module_name = renderer_module or ext
		renderer_module_import = 'powerline.renderers.{0}'.format(renderer_module_name)
		renderer_class_name = '{0}Renderer'.format(underscore_to_camelcase(renderer_module_name))
		try:
			Renderer = getattr(__import__(renderer_module_import, fromlist=[renderer_class_name]), renderer_class_name)
		except ImportError as e:
			sys.stderr.write('Error while importing renderer module: {0}\n'.format(e))
			sys.exit(1)
		options = {'term_truecolor': common_config.get('term_24bit_colors', False)}
		self.renderer = Renderer(theme_config, local_themes, theme_kwargs, colorscheme, **options)

	def get_config_paths(self):
		'''Get configuration paths.

		:return: list of paths
		'''
		config_home = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
		config_path = os.path.join(config_home, 'powerline')
		plugin_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config_files')
		return [config_path, plugin_path]

	def load_theme_config(self, name):
		'''Get theme configuration.

		:param str name:
			Name of the theme to load.

		:return: dictionary with :ref:`theme configuration <config-themes>`
		'''
		return load_json_config(self.config_paths, os.path.join('themes', self.ext, name))

	def load_main_config(self):
		'''Get top-level configuration.

		:return: dictionary with :ref:`top-level configuration <config-main>`.
		'''
		return load_json_config(self.config_paths, 'config')

	def load_colorscheme_config(self, name):
		'''Get colorscheme.

		:param str name:
			Name of the colorscheme to load.

		:return: dictionary with :ref:`colorscheme configuration <config-colorschemes>`.
		'''
		return load_json_config(self.config_paths, os.path.join('colorschemes', self.ext, name))

	def load_colors_config(self):
		'''Get colorscheme.

		:return: dictionary with :ref:`colors configuration <config-colors>`.
		'''
		return load_json_config(self.config_paths, 'colors')

	@staticmethod
	def get_local_themes(local_themes):
		'''Get local themes. No-op here, to be overridden in subclasses if
		required.

		:param dict local_themes:
			Usually accepts ``{matcher_name : theme_name}``.

		:return:
			anything accepted by ``self.renderer.get_theme`` and processable by
			``self.renderer.add_local_theme``. Renderer module is determined by
			``__init__`` arguments, refer to its documentation.
		'''
		return {}

	@staticmethod
	def get_segment_info():
		'''Get information for segments that require ``segment_info`` argument.
		To be overridden in subclasses.

		:return:
			anything accepted by segments as ``segment_info`` argument. Depends
			on the segments used, refer to Powerline subclass documentation.
		'''
		return None
