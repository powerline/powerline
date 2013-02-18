# -*- coding: utf-8 -*-

import importlib
import json
import os
import sys

from powerline.colorscheme import Colorscheme
from powerline.lib import underscore_to_camelcase


def load_json_config(search_paths, config_file):
	config_file += '.json'
	for path in search_paths:
		config_file_path = os.path.join(path, config_file)
		if os.path.isfile(config_file_path):
			with open(config_file_path, 'r') as config_file_fp:
				return json.load(config_file_fp)
	raise IOError('Config file not found in search path: {0}'.format(config_file))


class Powerline(object):
	def __init__(self, ext, renderer_module=None):
		self.config_paths = self.get_config_paths()

		# Load main config file
		config = self.load_main_config()
		common_config = config['common']
		ext_config = config['ext'][ext]
		self.ext = ext

		# Load and initialize colorscheme
		colorscheme_config = self.load_colorscheme_config(ext_config['colorscheme'])
		colorscheme = Colorscheme(colorscheme_config)

		# Load and initialize extension theme
		theme_config = self.load_theme_config(ext_config.get('theme', 'default'))
		common_config['paths'] = [os.path.expanduser(path) for path in common_config.get('paths', [])]
		self.import_paths = common_config['paths']
		theme_kwargs = {
			'ext': ext,
			'colorscheme': colorscheme,
			'common_config': common_config,
			'segment_info': self.get_segment_info(),
			}
		local_themes = self.get_local_themes(ext_config.get('local_themes', {}))

		# Load and initialize extension renderer
		renderer_module_name = renderer_module or ext
		renderer_module_import = 'powerline.renderers.{0}'.format(renderer_module_name)
		renderer_class_name = '{0}Renderer'.format(underscore_to_camelcase(renderer_module_name))
		try:
			Renderer = getattr(importlib.import_module(renderer_module_import), renderer_class_name)
		except ImportError as e:
			sys.stderr.write('Error while importing renderer module: {0}\n'.format(e))
			sys.exit(1)
		options = {'term_truecolor': common_config.get('term_24bit_colors', False)}
		self.renderer = Renderer(theme_config, local_themes, theme_kwargs, **options)

	def get_config_paths(self):
		config_home = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
		config_path = os.path.join(config_home, 'powerline')
		plugin_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config_files')
		return [config_path, plugin_path]

	def load_theme_config(self, name):
		return load_json_config(self.config_paths, os.path.join('themes', self.ext, name))

	def load_main_config(self):
		return load_json_config(self.config_paths, 'config')

	def load_colorscheme_config(self, name):
		return load_json_config(self.config_paths, os.path.join('colorschemes', self.ext, name))

	@staticmethod
	def get_local_themes(local_themes):
		return {}

	@staticmethod
	def get_segment_info():
		return None
