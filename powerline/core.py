# -*- coding: utf-8 -*-

import importlib
import json
import os
import sys

from colorscheme import Colorscheme
from theme import Theme


class Powerline(object):
	def __init__(self, ext):
		try:
			config_home = os.environ['XDG_CONFIG_HOME']
		except KeyError:
			config_home = os.path.expanduser('~/.config')

		config_path = os.path.join(config_home, 'powerline')
		plugin_path = os.path.realpath(os.path.dirname(__file__))
		self.search_paths = [config_path, plugin_path]

		sys.path[:0] = self.search_paths

		# Load main config file, limited to the current extension
		self.config = self._load_json_config('config')[ext]

		# Load and initialize colorscheme
		colorscheme_config = self._load_json_config(os.path.join('colorschemes', self.config['colorscheme']))
		self.colorscheme = Colorscheme(colorscheme_config)

		# Load and initialize extension theme
		theme_config = self._load_json_config(os.path.join('themes', ext, self.config['theme']))
		self.theme = Theme(ext, theme_config)

		# Load and initialize extension renderer
		renderer_module_name = 'powerline.ext.{0}.renderer'.format(ext)
		renderer_class_name = '{0}Renderer'.format(ext.capitalize())
		renderer_class = getattr(importlib.import_module(renderer_module_name), renderer_class_name)
		self.renderer = renderer_class(self.colorscheme, self.theme)

	def _load_json_config(self, config_file):
		config_file += '.json'
		for path in self.search_paths:
			config_file_path = os.path.join(path, config_file)
			if os.path.isfile(config_file_path):
				with open(config_file_path, 'rb') as config_file_fp:
					return json.load(config_file_fp)

		raise IOError('Config file not found in search path: {0}'.format(config_file))
