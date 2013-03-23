# vim:fileencoding=utf-8:noet

from __future__ import absolute_import
import json
import os
import sys
import copy

from powerline.colorscheme import Colorscheme
from powerline.lib.file_watcher import create_file_watcher

def open_file(path):
	return open(path, 'r')

class ConfigCache(object):

	def __init__(self):
		self.cache = {}
		self.file_changed = create_file_watcher()

	def __call__(self, search_paths, config_file, load=None, open_file=open_file):
		config_file += '.json'
		for path in search_paths:
			config_file_path = os.path.join(path, config_file)
			try:
				changed = self.file_changed(config_file_path)
			except OSError:
				continue

			if load is not None:
				with open_file(config_file_path) as f:
					return load(f)

			if changed:
				with open(config_file_path, 'rb') as f:
					self.cache[config_file_path] = json.loads(f.read().decode('utf-8'))
			# We return a copy because other code might modify the returned
			# object.
			return copy.deepcopy(self.cache[config_file_path])

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

	def __init__(self, ext, renderer_module=None, run_once=False):
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
			'run_once': run_once,
			}
		local_themes = self.get_local_themes(ext_config.get('local_themes'))

		# Load and initialize extension renderer
		renderer_module_name = renderer_module or ext
		renderer_module_import = 'powerline.renderers.{0}'.format(renderer_module_name)
		try:
			Renderer = __import__(renderer_module_import, fromlist=['renderer']).renderer
		except ImportError as e:
			sys.stderr.write('Error while importing renderer module: {0}\n'.format(e))
			sys.exit(1)
		options = {
			'term_truecolor': common_config.get('term_truecolor', False),
			'ambiwidth': common_config.get('ambiwidth', 1),
			'tmux_escape': common_config.get('additional_escapes') == 'tmux',
			'screen_escape': common_config.get('additional_escapes') == 'screen',
		}
		self.renderer = Renderer(theme_config, local_themes, theme_kwargs, colorscheme, **options)

	@staticmethod
	def get_config_paths():
		'''Get configuration paths.

		:return: list of paths
		'''
		config_home = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
		config_path = os.path.join(config_home, 'powerline')
		config_paths = [config_path]
		config_dirs = os.environ.get('XDG_CONFIG_DIRS', None)
		if config_dirs is not None:
			config_paths.extend([os.path.join(d, 'powerline') for d in config_dirs.split(':')])
		plugin_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config_files')
		config_paths.append(plugin_path)
		return config_paths

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
			Usually accepts ``{matcher_name : theme_name}``. May also receive
			None in case there is no local_themes configuration.

		:return:
			anything accepted by ``self.renderer.get_theme`` and processable by
			``self.renderer.add_local_theme``. Renderer module is determined by
			``__init__`` arguments, refer to its documentation.
		'''
		return None

	@staticmethod
	def get_segment_info():
		'''Get information for segments that require ``segment_info`` argument.
		To be overridden in subclasses.

		:return:
			anything accepted by segments as ``segment_info`` argument. Depends
			on the segments used, refer to Powerline subclass documentation.
		'''
		return None
