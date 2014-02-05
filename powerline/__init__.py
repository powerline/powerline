# vim:fileencoding=utf-8:noet

from __future__ import absolute_import
import os
import sys
import logging

from powerline.colorscheme import Colorscheme
from powerline.lib.config import ConfigLoader
from powerline.lib.unicode import safe_unicode, FailedUnicode
from powerline.config import DEFAULT_SYSTEM_CONFIG_DIR
from powerline.lib import mergedicts

from threading import Lock, Event


def _find_config_file(search_paths, config_file):
	config_file += '.json'
	for path in search_paths:
		config_file_path = os.path.join(path, config_file)
		if os.path.isfile(config_file_path):
			return config_file_path
	raise IOError('Config file not found in search path: {0}'.format(config_file))


class PowerlineLogger(object):
	def __init__(self, use_daemon_threads, logger, ext):
		self.logger = logger
		self.ext = ext
		self.use_daemon_threads = use_daemon_threads
		self.prefix = ''
		self.last_msgs = {}

	def _log(self, attr, msg, *args, **kwargs):
		prefix = kwargs.get('prefix') or self.prefix
		prefix = self.ext + ((':' + prefix) if prefix else '')
		if args or kwargs:
			msg = msg.format(*args, **kwargs)
		msg = prefix + ':' + safe_unicode(msg)
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


_fallback_logger = None


def get_fallback_logger():
	global _fallback_logger
	if _fallback_logger:
		return _fallback_logger

	log_format = '%(asctime)s:%(levelname)s:%(message)s'
	formatter = logging.Formatter(log_format)

	level = logging.WARNING
	handler = logging.StreamHandler()
	handler.setLevel(level)
	handler.setFormatter(formatter)

	logger = logging.getLogger('powerline')
	logger.setLevel(level)
	logger.addHandler(handler)
	_fallback_logger = PowerlineLogger(None, logger, '_fallback_')
	return _fallback_logger


def _generate_change_callback(lock, key, dictionary):
	def on_file_change(path):
		with lock:
			dictionary[key] = True
	return on_file_change


def get_config_paths():
	'''Get configuration paths from environment variables.

	Uses $XDG_CONFIG_HOME and $XDG_CONFIG_DIRS according to the XDG specification.

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


def generate_config_finder(get_config_paths=get_config_paths):
	'''Generate find_config_file function

	This function will find .json file given its path.

	:param function get_config_paths:
		Function that being called with no arguments will return a list of paths 
		that should be searched for configuration files.

	:return:
		Function that being given configuration file name will return full path 
		to it or raise IOError if it failed to find the file.
	'''
	config_paths = get_config_paths()
	return lambda cfg_path: _find_config_file(config_paths, cfg_path)


def load_config(cfg_path, find_config_file, config_loader, loader_callback=None):
	'''Load configuration file and setup watches

	Watches are only set up if loader_callback is not None.

	:param str cfg_path:
		Path for configuration file that should be loaded.
	:param function find_config_file:
		Function that finds configuration file. Check out the description of 
		the return value of ``generate_config_finder`` function.
	:param ConfigLoader config_loader:
		Configuration file loader class instance.
	:param function loader_callback:
		Function that will be called by config_loader when change to 
		configuration file is detected.

	:return: Configuration file contents.
	'''
	try:
		path = find_config_file(cfg_path)
	except IOError:
		if loader_callback:
			config_loader.register_missing(find_config_file, loader_callback, cfg_path)
		raise
	else:
		if loader_callback:
			config_loader.register(loader_callback, path)
		return config_loader.load(path)


def _get_log_handler(common_config):
	'''Get log handler.

	:param dict common_config:
		Configuration dictionary used to create handler.

	:return: logging.Handler subclass.
	'''
	log_file = common_config['log_file']
	if log_file:
		log_file = os.path.expanduser(log_file)
		log_dir = os.path.dirname(log_file)
		if not os.path.isdir(log_dir):
			os.mkdir(log_dir)
		return logging.FileHandler(log_file)
	else:
		return logging.StreamHandler()


def create_logger(common_config):
	'''Create logger according to provided configuration
	'''
	log_format = common_config['log_format']
	formatter = logging.Formatter(log_format)

	level = getattr(logging, common_config['log_level'])
	handler = _get_log_handler(common_config)
	handler.setLevel(level)
	handler.setFormatter(formatter)

	logger = logging.getLogger('powerline')
	logger.setLevel(level)
	logger.addHandler(handler)
	return logger


def finish_common_config(common_config):
	'''Add default values to common config and expand ~ in paths

	:param dict common_config:
		Common configuration, as it was just loaded.

	:return:
		Copy of common configuration with all configuration keys and expanded 
		paths.
	'''
	common_config = common_config.copy()
	common_config.setdefault('paths', [])
	common_config.setdefault('watcher', 'auto')
	common_config.setdefault('log_level', 'WARNING')
	common_config.setdefault('log_format', '%(asctime)s:%(levelname)s:%(message)s')
	common_config.setdefault('term_truecolor', False)
	common_config.setdefault('ambiwidth', 1)
	common_config.setdefault('additional_escapes', None)
	common_config.setdefault('reload_config', True)
	common_config.setdefault('interval', None)
	common_config.setdefault('log_file', None)

	common_config['paths'] = [
		os.path.expanduser(path) for path in common_config['paths']
	]

	return common_config


if sys.version_info < (3,):
	# `raise exception[0], None, exception[1]` is a SyntaxError in python-3*
	# Not using ('''…''') because this syntax does not work in python-2.6
	exec(('def reraise(exception):\n'
			'	if type(exception) is tuple:\n'
			'		raise exception[0], None, exception[1]\n'
			'	else:\n'
			'		raise exception\n'))
else:
	def reraise(exception):
		if type(exception) is tuple:
			raise exception[0].with_traceback(exception[1])
		else:
			raise exception


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
		If this parameter contains a dot, ``powerline.renderers.`` is not 
		prepended. There is also a special case for renderers defined in 
		toplevel modules: ``foo.`` (note: dot at the end) tries to get renderer 
		from module ``foo`` (because ``foo`` (without dot) tries to get renderer 
		from module ``powerline.renderers.foo``).
	:param bool run_once:
		Determines whether .renderer.render() method will be run only once 
		during python session.
	:param Logger logger:
		If present, no new logger will be created and this logger will be used.
	:param bool use_daemon_threads:
		Use daemon threads for.
	:param Event shutdown_event:
		Use this Event as shutdown_event.
	:param ConfigLoader config_loader:
		Class that manages (re)loading of configuration.
	'''

	def __init__(self,
				ext,
				renderer_module=None,
				run_once=False,
				logger=None,
				use_daemon_threads=True,
				shutdown_event=None,
				config_loader=None):
		self.ext = ext
		self.renderer_module = renderer_module or ext
		self.run_once = run_once
		self.logger = logger
		self.use_daemon_threads = use_daemon_threads

		if '.' not in self.renderer_module:
			self.renderer_module = 'powerline.renderers.' + self.renderer_module
		elif self.renderer_module[-1] == '.':
			self.renderer_module = self.renderer_module[:-1]

		self.find_config_file = generate_config_finder(self.get_config_paths)

		self.cr_kwargs_lock = Lock()
		self.cr_kwargs = {}
		self.cr_callbacks = {}
		for key in ('main', 'colors', 'colorscheme', 'theme'):
			self.cr_kwargs['load_' + key] = True
			self.cr_callbacks[key] = _generate_change_callback(
				self.cr_kwargs_lock,
				'load_' + key,
				self.cr_kwargs
			)

		self.shutdown_event = shutdown_event or Event()
		self.config_loader = config_loader or ConfigLoader(shutdown_event=self.shutdown_event, run_once=run_once)
		self.run_loader_update = False

		self.renderer_options = {}

		self.prev_common_config = None
		self.prev_ext_config = None
		self.pl = None

	def create_renderer(self, load_main=False, load_colors=False, load_colorscheme=False, load_theme=False):
		'''(Re)create renderer object. Can be used after Powerline object was 
		successfully initialized. If any of the below parameters except 
		``load_main`` is True renderer object will be recreated.

		:param bool load_main:
			Determines whether main configuration file (:file:`config.json`) 
			should be loaded. If appropriate configuration changes implies 
			``load_colorscheme`` and ``load_theme`` and recreation of renderer 
			object. Won’t trigger recreation if only unrelated configuration 
			changed.
		:param bool load_colors:
			Determines whether colors configuration from :file:`colors.json` 
			should be (re)loaded.
		:param bool load_colorscheme:
			Determines whether colorscheme configuration should be (re)loaded.
		:param bool load_theme:
			Determines whether theme configuration should be reloaded.
		'''
		common_config_differs = False
		ext_config_differs = False
		if load_main:
			self._purge_configs('main')
			config = self.load_main_config()
			self.common_config = config['common']
			if self.common_config != self.prev_common_config:
				common_config_differs = True

				self.prev_common_config = self.common_config

				self.common_config = finish_common_config(self.common_config)

				self.import_paths = self.common_config['paths']

				if not self.logger:
					self.logger = create_logger(self.common_config)

				if not self.pl:
					self.pl = PowerlineLogger(self.use_daemon_threads, self.logger, self.ext)
					self.config_loader.pl = self.pl

				if not self.run_once:
					self.config_loader.set_watcher(self.common_config['watcher'])

				self.renderer_options.update(
					pl=self.pl,
					term_truecolor=self.common_config['term_truecolor'],
					ambiwidth=self.common_config['ambiwidth'],
					tmux_escape=self.common_config['additional_escapes'] == 'tmux',
					screen_escape=self.common_config['additional_escapes'] == 'screen',
					theme_kwargs={
						'ext': self.ext,
						'common_config': self.common_config,
						'run_once': self.run_once,
						'shutdown_event': self.shutdown_event,
					},
				)

				if not self.run_once and self.common_config['reload_config']:
					interval = self.common_config['interval']
					self.config_loader.set_interval(interval)
					self.run_loader_update = (interval is None)
					if interval is not None and not self.config_loader.is_alive():
						self.config_loader.start()

			self.ext_config = config['ext'][self.ext]
			if self.ext_config != self.prev_ext_config:
				ext_config_differs = True
				if not self.prev_ext_config or self.ext_config.get('local_themes') != self.prev_ext_config.get('local_themes'):
					self.renderer_options['local_themes'] = self.get_local_themes(self.ext_config.get('local_themes'))
				load_colorscheme = (load_colorscheme
							or not self.prev_ext_config
							or self.prev_ext_config['colorscheme'] != self.ext_config['colorscheme'])
				load_theme = (load_theme
							or not self.prev_ext_config
							or self.prev_ext_config['theme'] != self.ext_config['theme'])
				self.prev_ext_config = self.ext_config

		create_renderer = load_colors or load_colorscheme or load_theme or common_config_differs or ext_config_differs

		if load_colors:
			self._purge_configs('colors')
			self.colors_config = self.load_colors_config()

		if load_colorscheme or load_colors:
			self._purge_configs('colorscheme')
			if load_colorscheme:
				self.colorscheme_config = self.load_colorscheme_config(self.ext_config['colorscheme'])
			self.renderer_options['colorscheme'] = Colorscheme(self.colorscheme_config, self.colors_config)

		if load_theme:
			self._purge_configs('theme')
			self.renderer_options['theme_config'] = self.load_theme_config(self.ext_config.get('theme', 'default'))

		if create_renderer:
			try:
				Renderer = __import__(self.renderer_module, fromlist=['renderer']).renderer
			except Exception as e:
				self.exception('Failed to import renderer module: {0}', str(e))
				sys.exit(1)

			# Renderer updates configuration file via segments’ .startup thus it 
			# should be locked to prevent state when configuration was updated, 
			# but .render still uses old renderer.
			try:
				renderer = Renderer(**self.renderer_options)
			except Exception as e:
				self.exception('Failed to construct renderer object: {0}', str(e))
				if not hasattr(self, 'renderer'):
					raise
			else:
				self.renderer = renderer

	@staticmethod
	def get_config_paths():
		'''Get configuration paths.

		Should be overridden in subclasses in order to provide a way to override 
		used paths.

		:return: list of paths
		'''
		return get_config_paths()

	def _load_config(self, cfg_path, type):
		'''Load configuration and setup watches.'''
		return load_config(
			cfg_path,
			self.find_config_file,
			self.config_loader,
			self.cr_callbacks[type]
		)

	def _purge_configs(self, type):
		function = self.cr_callbacks[type]
		self.config_loader.unregister_functions(set((function,)))
		self.config_loader.unregister_missing(set(((self.find_config_file, function),)))

	def load_theme_config(self, name):
		'''Get theme configuration.

		:param str name:
			Name of the theme to load.

		:return: dictionary with :ref:`theme configuration <config-themes>`
		'''
		return self._load_config(os.path.join('themes', self.ext, name), 'theme')

	def load_main_config(self):
		'''Get top-level configuration.

		:return: dictionary with :ref:`top-level configuration <config-main>`.
		'''
		return self._load_config('config', 'main')

	def load_colorscheme_config(self, name):
		'''Get colorscheme.

		:param str name:
			Name of the colorscheme to load.

		:return: dictionary with :ref:`colorscheme configuration <config-colorschemes>`.
		'''
		# TODO Make sure no colorscheme name ends with __ (do it in 
		# powerline-lint)
		levels = (
			os.path.join('colorschemes', name),
			os.path.join('colorschemes', self.ext, '__main__'),
			os.path.join('colorschemes', self.ext, name),
		)
		config = {}
		loaded = 0
		exceptions = []
		for cfg_path in levels:
			try:
				lvl_config = self._load_config(cfg_path, 'colorscheme')
			except IOError as e:
				if sys.version_info < (3,):
					tb = sys.exc_info()[2]
					exceptions.append((e, tb))
				else:
					exceptions.append(e)
			else:
				if not cfg_path.endswith('__'):
					loaded += 1
				# TODO Either make sure `attr` list is always present or make 
				# mergedicts not merge group definitions.
				mergedicts(config, lvl_config)
		if not loaded:
			for exception in exceptions:
				if type(exception) is tuple:
					e = exception[0]
				else:
					e = exception
				self.exception('Failed to load colorscheme: {0}', e, exception=exception)
			raise e
		return config

	def load_colors_config(self):
		'''Get colorscheme.

		:return: dictionary with :ref:`colors configuration <config-colors>`.
		'''
		return self._load_config('colors', 'colors')

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

	def update_renderer(self):
		'''Updates/creates a renderer if needed.'''
		if self.run_loader_update:
			self.config_loader.update()
		cr_kwargs = None
		with self.cr_kwargs_lock:
			if self.cr_kwargs:
				cr_kwargs = self.cr_kwargs.copy()
		if cr_kwargs:
			try:
				self.create_renderer(**cr_kwargs)
			except Exception as e:
				self.exception('Failed to create renderer: {0}', str(e))
				if hasattr(self, 'renderer'):
					with self.cr_kwargs_lock:
						self.cr_kwargs.clear()
				else:
					raise
			else:
				with self.cr_kwargs_lock:
					self.cr_kwargs.clear()

	def render(self, *args, **kwargs):
		'''Update/create renderer if needed and pass all arguments further to 
		``self.renderer.render()``.
		'''
		try:
			self.update_renderer()
			return self.renderer.render(*args, **kwargs)
		except Exception as e:
			try:
				self.exception('Failed to render: {0}', str(e))
			except Exception as e:
				# Updates e variable to new value, masking previous one. 
				# Normally it is the same exception (due to raise in case pl is 
				# unset), but it may also show error in logger. Note that latter 
				# is not logged by logger for obvious reasons, thus this also 
				# prevents us from seeing logger traceback.
				pass
			return FailedUnicode(safe_unicode(e))

	def render_above_lines(self, *args, **kwargs):
		'''Like .render(), but for ``self.renderer.render_above_lines()``
		'''
		try:
			self.update_renderer()
			for line in self.renderer.render_above_lines(*args, **kwargs):
				yield line
		except Exception as e:
			try:
				self.exception('Failed to render: {0}', str(e))
			except Exception as e:
				# Updates e variable to new value, masking previous one. 
				# Normally it is the same exception (due to raise in case pl is 
				# unset), but it may also show error in logger. Note that latter 
				# is not logged by logger for obvious reasons, thus this also 
				# prevents us from seeing logger traceback.
				pass
			yield FailedUnicode(safe_unicode(e))

	def shutdown(self):
		'''Shut down all background threads. Must be run only prior to exiting 
		current application.
		'''
		self.shutdown_event.set()
		try:
			self.renderer.shutdown()
		except AttributeError:
			pass
		functions = tuple(self.cr_callbacks.values())
		self.config_loader.unregister_functions(set(functions))
		self.config_loader.unregister_missing(set(((self.find_config_file, function) for function in functions)))

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.shutdown()

	def exception(self, msg, *args, **kwargs):
		if 'prefix' not in kwargs:
			kwargs['prefix'] = 'powerline'
		exception = kwargs.pop('exception', None)
		pl = getattr(self, 'pl', None) or get_fallback_logger()
		if exception:
			try:
				reraise(exception)
			except Exception:
				return pl.exception(msg, *args, **kwargs)
		return pl.exception(msg, *args, **kwargs)
