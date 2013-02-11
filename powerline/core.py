# -*- coding: utf-8 -*-

import importlib
import json
import os
import sys

from powerline.colorscheme import Colorscheme
from powerline.matcher import Matcher
from powerline.lib import underscore_to_camelcase


class Powerline(object):
	def __init__(self, ext, renderer_module=None, segment_info=None, renderer_options={}):
		config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
		config_path = os.path.join(config_home, 'powerline')
		plugin_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config_files')
		self.search_paths = [config_path, plugin_path]
		sys.path[:0] = self.search_paths

		# Load main config file
		config = self._load_json_config('config')
		self.config = config['common']
		self.config_ext = config['ext'][ext]

		# Load and initialize colorscheme
		colorscheme_config = self._load_json_config(os.path.join('colorschemes', ext, self.config_ext['colorscheme']))
		colorscheme = Colorscheme(colorscheme_config)

		# Load and initialize extension theme
		theme_config = self._load_theme_config(ext, self.config_ext.get('theme', 'default'))
		self.config['paths'] = [os.path.expanduser(path) for path in self.config.get('paths', [])]
		self.get_matcher = Matcher(ext, self.config['paths']).get
		theme_kwargs = {
			'ext': ext,
			'colorscheme': colorscheme,
			'common_config': self.config,
			'segment_info': segment_info,
			}
		local_themes = {}
		for key, local_theme_name in self.config_ext.get('local_themes', {}).items():
			key = self.get_matcher(key)
			local_themes[key] = {'config': self._load_theme_config(ext, local_theme_name)}

		# Load and initialize extension renderer
		renderer_module_name = renderer_module or ext
		renderer_module_import = 'powerline.renderers.{0}'.format(renderer_module_name)
		renderer_class_name = '{0}Renderer'.format(underscore_to_camelcase(renderer_module_name))
		try:
			Renderer = getattr(importlib.import_module(renderer_module_import), renderer_class_name)
		except ImportError as e:
			sys.stderr.write('Error while importing renderer module: {0}\n'.format(e))
			sys.exit(1)
		options = {'term_truecolor': self.config.get('term_24bit_colors', False)}
		options.update(renderer_options)
		self.renderer = Renderer(theme_config, local_themes, theme_kwargs, **options)

	def add_local_theme(self, key, config):
		'''Add local themes at runtime (e.g. during vim session).

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

	def _load_theme_config(self, ext, name):
		return self._load_json_config(os.path.join('themes', ext, name))

	def _load_json_config(self, config_file):
		config_file += '.json'
		for path in self.search_paths:
			config_file_path = os.path.join(path, config_file)
			if os.path.isfile(config_file_path):
				with open(config_file_path, 'r') as config_file_fp:
					return json.load(config_file_fp)
		raise IOError('Config file not found in search path: {0}'.format(config_file))
