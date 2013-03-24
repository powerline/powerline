# vim:fileencoding=utf-8:noet

from __future__ import absolute_import
import json
import os
import sys
import logging

from powerline.colorscheme import Colorscheme


DEFAULT_SYSTEM_CONFIG_DIR = None


def open_file(path):
	return open(path, 'r')


def load_json_config(search_paths, config_file, load=json.load, open_file=open_file):
	config_file += '.json'
	for path in search_paths:
		config_file_path = os.path.join(path, config_file)
		if os.path.isfile(config_file_path):
			with open_file(config_file_path) as config_file_fp:
				return load(config_file_fp)
	raise IOError('Config file not found in search path: {0}'.format(config_file))


class PowerlineState(object):
	def __init__(self, logger, environ, getcwd, home):
		self.environ = environ
		self.getcwd = getcwd
		self.home = home or environ.get('HOME', None)
		self.logger = logger
		self.prefix = None
		self.last_msgs = {}

	def _log(self, attr, msg, *args, **kwargs):
		prefix = kwargs.get('prefix') or self.prefix
		msg = ((prefix + ':') if prefix else '') + msg.format(*args, **kwargs)
		key = attr + ':' + prefix
		if msg != self.last_msgs.get(key):
			getattr(self.logger, attr)(msg)
			self.last_msgs[key] = msg

	def critical(self, msg, *args, **kwargs):
		self._log('critical', msg, *args, **kwargs)

	def exception(self, msg, *args, **kwargs):
		self._log('exception', msg, *args, **kwargs)

	def info(self, msg, *args, **kwargs):
		self._log('info', msg, *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		self._log('error', msg, *args, **kwargs)

	def warn(self, msg, *args, **kwargs):
		self._log('warning', msg, *args, **kwargs)

	def debug(self, msg, *args, **kwargs):
		self._log('debug', msg, *args, **kwargs)


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
	:param bool run_once:
		Determines whether .renderer.render() method will be run only once 
		during python session.
	:param Logger logger:
		If present, no new logger will be created and this logger will be used.
	:param dict environ:
		Object with ``.__getitem__`` and ``.get`` methods used to obtain 
		environment variables. Defaults to ``os.environ``.
	:param func getcwd:
		Function used to get current working directory. Defaults to 
		``os.getcwdu`` or ``os.getcwd``.
	:param str home:
		Home directory. Defaults to ``environ.get('HOME')``.
	'''

	def __init__(self,
				ext,
				renderer_module=None,
				run_once=False,
				logger=None,
				environ=os.environ,
				getcwd=getattr(os, 'getcwdu', os.getcwd),
				home=None):
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

		# Create logger
		if not logger:
			log_format = common_config.get('log_format', '%(asctime)s:%(levelname)s:%(message)s')
			formatter = logging.Formatter(log_format)

			level = getattr(logging, common_config.get('log_level', 'WARNING'))
			handler = self.get_log_handler(common_config)
			handler.setLevel(level)
			handler.setFormatter(formatter)

			logger = logging.getLogger('powerline')
			logger.setLevel(level)
			logger.addHandler(handler)

		pl = PowerlineState(logger=logger, environ=environ, getcwd=getcwd, home=home)

		self.renderer = Renderer(theme_config, local_themes, theme_kwargs, colorscheme, pl, **options)

	def get_log_handler(self, common_config):
		'''Get log handler.

		:param dict common_config:
			Common configuration.

		:return: logging.Handler subclass.
		'''
		log_file = common_config.get('log_file', None)
		if log_file:
			log_file = os.path.expanduser(log_file)
			log_dir = os.path.dirname(log_file)
			if not os.path.isdir(log_dir):
				os.mkdir(log_dir)
			return logging.FileHandler(log_file)
		else:
			return logging.StreamHandler()

	@staticmethod
	def get_config_paths():
		'''Get configuration paths.

		:return: list of paths
		'''
		config_home = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
		config_path = os.path.join(config_home, 'powerline')
		config_paths = [config_path]
		config_dirs = os.environ.get('XDG_CONFIG_DIRS', DEFAULT_SYSTEM_CONFIG_DIR)
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
