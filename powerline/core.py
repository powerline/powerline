# -*- coding: utf-8 -*-

import importlib
import json
import os
import sys

from colorscheme import Colorscheme
from segments import Segments
from matchers import Matchers


class Powerline(object):
	def __init__(self, ext):
		config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

		config_path = os.path.join(config_home, 'powerline')
		plugin_path = os.path.realpath(os.path.dirname(__file__))
		self.search_paths = [config_path, plugin_path]

		sys.path[:0] = self.search_paths

		# Load main config file
		config = self._load_json_config('config')
		self.config = config['common']
		self.config_ext = config['ext'][ext]

		# Load and initialize colorscheme
		colorscheme_config = self._load_json_config(os.path.join('colorschemes', self.config_ext['colorscheme']))
		colorscheme = Colorscheme(colorscheme_config)

		# Load and initialize extension theme
		theme_config = self._load_theme_config(ext, self.config_ext.get('theme', 'default'))

		path = [os.path.expanduser(path) for path in self.config.get('paths', [])]

		get_segment = Segments(ext, path, colorscheme).get
		get_matcher = Matchers(ext, path).get

		theme_kwargs = {
				'ext': ext,
				'colorscheme': colorscheme,
				'common_config': self.config,
				'get_segment': get_segment
			}

		local_themes = {}
		for key, local_theme_name in self.config_ext.get('local_themes', {}).iteritems():
			key = get_matcher(key)
			local_themes[key] = {'config': self._load_theme_config(ext, local_theme_name)}

		# Load and initialize extension renderer
		renderer_module_name = 'powerline.ext.{0}.renderer'.format(ext)
		renderer_class_name = '{0}Renderer'.format(ext.capitalize())
		Renderer = getattr(importlib.import_module(renderer_module_name), renderer_class_name)
		self.renderer = Renderer(theme_config, local_themes, theme_kwargs)

	def _load_theme_config(self, ext, name):
		return self._load_json_config(os.path.join('themes', ext, name))

	def _load_json_config(self, config_file):
		config_file += '.json'
		for path in self.search_paths:
			config_file_path = os.path.join(path, config_file)
			if os.path.isfile(config_file_path):
				with open(config_file_path, 'rb') as config_file_fp:
					return json.load(config_file_fp)

		raise IOError('Config file not found in search path: {0}'.format(config_file))
# vim: noet tw=120
