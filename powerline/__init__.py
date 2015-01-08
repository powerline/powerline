# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import logging

from threading import Lock, Event

from powerline.colorscheme import Colorscheme
from powerline.lib.config import ConfigLoader
from powerline.lib.unicode import safe_unicode, FailedUnicode
from powerline.config import DEFAULT_SYSTEM_CONFIG_DIR
from powerline.lib.dict import mergedicts
from powerline.lib.encoding import get_preferred_output_encoding
from powerline.lib.path import join


class NotInterceptedError(BaseException):
	pass


def _config_loader_condition(path):
	if path and os.path.isfile(path):
		return path
	return None


def _find_config_files(search_paths, config_file, config_loader=None, loader_callback=None):
	config_file += '.json'
	found = False
	for path in search_paths:
		config_file_path = join(path, config_file)
		if os.path.isfile(config_file_path):
			yield config_file_path
			found = True
		elif config_loader:
			config_loader.register_missing(_config_loader_condition, loader_callback, config_file_path)
	if not found:
		raise IOError('Config file not found in search paths ({0}): {1}'.format(
			', '.join(search_paths),
			config_file
		))


class PowerlineLogger(object):
	'''Proxy class for logging.Logger instance

	It emits messages in format ``{ext}:{prefix}:{message}`` where

	``{ext}``
		is a used powerline extension (e.g. “vim”, “shell”, “ipython”).
	``{prefix}``
		is a local prefix, usually a segment name.
	``{message}``
		is the original message passed to one of the logging methods.

	Each of the methods (``critical``, ``exception``, ``info``, ``error``, 
	``warn``, ``debug``) expects to receive message in an ``str.format`` format, 
	not in printf-like format.

	Log is saved to the location :ref:`specified by user <config-common-log>`.
	'''

	def __init__(self, use_daemon_threads, logger, ext):
		self.logger = logger
		self.ext = ext
		self.use_daemon_threads = use_daemon_threads
		self.prefix = ''
		self.last_msgs = {}

	def _log(self, attr, msg, *args, **kwargs):
		prefix = kwargs.get('prefix') or self.prefix
		prefix = self.ext + ((':' + prefix) if prefix else '')
		msg = safe_unicode(msg)
		if args or kwargs:
			args = [safe_unicode(s) if isinstance(s, bytes) else s for s in args]
			kwargs = dict((
				(k, safe_unicode(v) if isinstance(v, bytes) else v)
				for k, v in kwargs.items()
			))
			msg = msg.format(*args, **kwargs)
		msg = prefix + ':' + msg
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


def get_fallback_logger(stream=None):
	global _fallback_logger
	if _fallback_logger:
		return _fallback_logger

	log_format = '%(asctime)s:%(levelname)s:%(message)s'
	formatter = logging.Formatter(log_format)

	level = logging.WARNING
	handler = logging.StreamHandler(stream)
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
	config_path = join(config_home, 'powerline')
	config_paths = [config_path]
	config_dirs = os.environ.get('XDG_CONFIG_DIRS', DEFAULT_SYSTEM_CONFIG_DIR)
	if config_dirs is not None:
		config_paths[:0] = reversed([join(d, 'powerline') for d in config_dirs.split(':')])
	plugin_path = join(os.path.realpath(os.path.dirname(__file__)), 'config_files')
	config_paths.insert(0, plugin_path)
	return config_paths


def generate_config_finder(get_config_paths=get_config_paths):
	'''Generate find_config_files function

	This function will find .json file given its path.

	:param function get_config_paths:
		Function that being called with no arguments will return a list of paths 
		that should be searched for configuration files.

	:return:
		Function that being given configuration file name will return full path 
		to it or raise IOError if it failed to find the file.
	'''
	config_paths = get_config_paths()
	return lambda *args: _find_config_files(config_paths, *args)


def load_config(cfg_path, find_config_files, config_loader, loader_callback=None):
	'''Load configuration file and setup watches

	Watches are only set up if loader_callback is not None.

	:param str cfg_path:
		Path for configuration file that should be loaded.
	:param function find_config_files:
		Function that finds configuration file. Check out the description of 
		the return value of ``generate_config_finder`` function.
	:param ConfigLoader config_loader:
		Configuration file loader class instance.
	:param function loader_callback:
		Function that will be called by config_loader when change to 
		configuration file is detected.

	:return: Configuration file contents.
	'''
	found_files = find_config_files(cfg_path, config_loader, loader_callback)
	ret = None
	for path in found_files:
		if loader_callback:
			config_loader.register(loader_callback, path)
		if ret is None:
			ret = config_loader.load(path)
		else:
			mergedicts(ret, config_loader.load(path))
	return ret


def _get_log_handler(common_config, stream=None):
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
		return logging.StreamHandler(stream)


def create_logger(common_config, stream=None):
	'''Create logger according to provided configuration
	'''
	log_format = common_config['log_format']
	formatter = logging.Formatter(log_format)

	level = getattr(logging, common_config['log_level'])
	handler = _get_log_handler(common_config, stream)
	handler.setLevel(level)
	handler.setFormatter(formatter)

	logger = logging.getLogger('powerline')
	logger.setLevel(level)
	logger.addHandler(handler)
	return logger


def finish_common_config(encoding, common_config):
	'''Add default values to common config and expand ~ in paths

	:param dict common_config:
		Common configuration, as it was just loaded.

	:return:
		Copy of common configuration with all configuration keys and expanded 
		paths.
	'''
	encoding = encoding.lower()
	if encoding.startswith('utf') or encoding.startswith('ucs'):
		default_top_theme = 'powerline'
	else:
		default_top_theme = 'ascii'

	common_config = common_config.copy()
	common_config.setdefault('default_top_theme', default_top_theme)
	common_config.setdefault('paths', [])
	common_config.setdefault('watcher', 'auto')
	common_config.setdefault('log_level', 'WARNING')
	common_config.setdefault('log_format', '%(asctime)s:%(levelname)s:%(message)s')
	common_config.setdefault('term_truecolor', False)
	common_config.setdefault('term_escape_style', 'auto')
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
	exec((
		'def reraise(exception):\n'
		'	if type(exception) is tuple:\n'
		'		raise exception[0], None, exception[1]\n'
		'	else:\n'
		'		raise exception\n'
	))
else:
	def reraise(exception):
		if type(exception) is tuple:
			raise exception[0].with_traceback(exception[1])
		else:
			raise exception


def gen_module_attr_getter(pl, import_paths, imported_modules):
	def get_module_attr(module, attr, prefix='powerline'):
		'''Import module and get its attribute.

		Replaces ``from {module} import {attr}``.

		:param str module:
			Module name, will be passed as first argument to ``__import__``.
		:param str attr:
			Module attribute, will be passed to ``__import__`` as the only value 
			in ``fromlist`` tuple.

		:return:
			Attribute value or ``None``. Note: there is no way to distinguish 
			between successfull import of attribute equal to ``None`` and 
			unsuccessfull import.
		'''
		oldpath = sys.path
		sys.path = import_paths + sys.path
		module = str(module)
		attr = str(attr)
		try:
			imported_modules.add(module)
			return getattr(__import__(module, fromlist=(attr,)), attr)
		except Exception as e:
			pl.exception('Failed to import attr {0} from module {1}: {2}', attr, module, str(e), prefix=prefix)
			return None
		finally:
			sys.path = oldpath

	return get_module_attr


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
		the package imported like this: ``powerline.renderers.{render_module}``. 
		If this parameter contains a dot ``powerline.renderers.`` is not 
		prepended. There is also a special case for renderers defined in 
		toplevel modules: ``foo.`` (note: dot at the end) tries to get renderer 
		from module ``foo`` (because ``foo`` (without dot) tries to get renderer 
		from module ``powerline.renderers.foo``). When ``.foo`` (with leading 
		dot) variant is used ``renderer_module`` will be 
		``powerline.renderers.{ext}{renderer_module}``.
	:param bool run_once:
		Determines whether :py:meth:`render` method will be run only once 
		during python session.
	:param Logger logger:
		If present no new logger will be created and the provided logger will be 
		used.
	:param bool use_daemon_threads:
		When creating threads make them daemon ones.
	:param Event shutdown_event:
		Use this Event as shutdown_event instead of creating new event.
	:param ConfigLoader config_loader:
		Instance of the class that manages (re)loading of the configuration.
	'''

	def __init__(self, *args, **kwargs):
		self.init_args = (args, kwargs)
		self.init(*args, **kwargs)

	def init(self,
	         ext,
	         renderer_module=None,
	         run_once=False,
	         logger=None,
	         use_daemon_threads=True,
	         shutdown_event=None,
	         config_loader=None):
		'''Do actual initialization.

		__init__ function only stores the arguments and runs this function. This 
		function exists for powerline to be able to reload itself: it is easier 
		to make ``__init__`` store arguments and call overriddable ``init`` than 
		tell developers that each time they override Powerline.__init__ in 
		subclasses they must store actual arguments.
		'''
		self.ext = ext
		self.run_once = run_once
		self.logger = logger
		self.use_daemon_threads = use_daemon_threads

		if not renderer_module:
			self.renderer_module = 'powerline.renderers.' + ext
		elif '.' not in renderer_module:
			self.renderer_module = 'powerline.renderers.' + renderer_module
		elif renderer_module.startswith('.'):
			self.renderer_module = 'powerline.renderers.' + ext + renderer_module
		elif renderer_module.endswith('.'):
			self.renderer_module = renderer_module[:-1]
		else:
			self.renderer_module = renderer_module

		self.find_config_files = generate_config_finder(self.get_config_paths)

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
		self.setup_args = ()
		self.setup_kwargs = {}
		self.imported_modules = set()

	get_encoding = staticmethod(get_preferred_output_encoding)
	'''Get encoding used by the current application

	Usually returns encoding of the current locale.
	'''

	def create_logger(self):
		'''Create logger

		This function is used to create logger unless it was already specified 
		at initialization.
		'''
		return create_logger(self.common_config, self.default_log_stream)

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
			self.common_config = finish_common_config(self.get_encoding(), config['common'])
			if self.common_config != self.prev_common_config:
				common_config_differs = True

				load_theme = (load_theme
					or not self.prev_common_config
					or self.prev_common_config['default_top_theme'] != self.common_config['default_top_theme'])

				self.prev_common_config = self.common_config

				self.import_paths = self.common_config['paths']

				if not self.logger:
					self.logger = self.create_logger()

				if not self.pl:
					self.pl = PowerlineLogger(self.use_daemon_threads, self.logger, self.ext)
					self.config_loader.pl = self.pl

				if not self.run_once:
					self.config_loader.set_watcher(self.common_config['watcher'])

				self.get_module_attr = gen_module_attr_getter(self.pl, self.import_paths, self.imported_modules)

				mergedicts(self.renderer_options, dict(
					pl=self.pl,
					term_truecolor=self.common_config['term_truecolor'],
					term_escape_style=self.common_config['term_escape_style'],
					ambiwidth=self.common_config['ambiwidth'],
					tmux_escape=self.common_config['additional_escapes'] == 'tmux',
					screen_escape=self.common_config['additional_escapes'] == 'screen',
					theme_kwargs={
						'ext': self.ext,
						'common_config': self.common_config,
						'run_once': self.run_once,
						'shutdown_event': self.shutdown_event,
						'get_module_attr': self.get_module_attr,
					},
				))

				if not self.run_once and self.common_config['reload_config']:
					interval = self.common_config['interval']
					self.config_loader.set_interval(interval)
					self.run_loader_update = (interval is None)
					if interval is not None and not self.config_loader.is_alive():
						self.config_loader.start()

			self.ext_config = config['ext'][self.ext]

			top_theme = (
				self.ext_config.get('top_theme')
				or self.common_config['default_top_theme']
			)
			self.theme_levels = (
				os.path.join('themes', top_theme),
				os.path.join('themes', self.ext, '__main__'),
			)
			self.renderer_options['theme_kwargs']['top_theme'] = top_theme

			if self.ext_config != self.prev_ext_config:
				ext_config_differs = True
				if (
					not self.prev_ext_config
					or self.ext_config.get('components') != self.prev_ext_config.get('components')
				):
					self.setup_components(self.ext_config.get('components'))
				if (
					not self.prev_ext_config
					or self.ext_config.get('local_themes') != self.prev_ext_config.get('local_themes')
				):
					self.renderer_options['local_themes'] = self.get_local_themes(self.ext_config.get('local_themes'))
				load_colorscheme = (
					load_colorscheme
					or not self.prev_ext_config
					or self.prev_ext_config['colorscheme'] != self.ext_config['colorscheme']
				)
				load_theme = (
					load_theme
					or not self.prev_ext_config
					or self.prev_ext_config['theme'] != self.ext_config['theme']
				)
				self.prev_ext_config = self.ext_config

		create_renderer = load_colors or load_colorscheme or load_theme or common_config_differs or ext_config_differs

		if load_colors:
			self._purge_configs('colors')
			self.colors_config = self.load_colors_config()

		if load_colorscheme or load_colors:
			self._purge_configs('colorscheme')
			if load_colorscheme:
				self.colorscheme_config = self.load_colorscheme_config(self.ext_config['colorscheme'])
			self.renderer_options['theme_kwargs']['colorscheme'] = (
				Colorscheme(self.colorscheme_config, self.colors_config))

		if load_theme:
			self._purge_configs('theme')
			self.renderer_options['theme_config'] = self.load_theme_config(self.ext_config.get('theme', 'default'))

		if create_renderer:
			Renderer = self.get_module_attr(self.renderer_module, 'renderer')
			if not Renderer:
				if hasattr(self, 'renderer'):
					return
				else:
					raise ImportError('Failed to obtain renderer')

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

	default_log_stream = sys.stdout
	'''Default stream for default log handler

	Usually it is ``sys.stderr``, but there is sometimes a reason to prefer 
	``sys.stdout`` or a custom file-like object. It is not supposed to be used 
	to write to some file.
	'''

	def setup_components(self, components):
		'''Run component-specific setup

		:param set components:
			Set of the enabled componets or None.

		Should be overridden by subclasses.
		'''
		pass

	@staticmethod
	def get_config_paths():
		'''Get configuration paths.

		Should be overridden in subclasses in order to provide a way to override 
		used paths.

		:return: list of paths
		'''
		return get_config_paths()

	def load_config(self, cfg_path, cfg_type):
		'''Load configuration and setup watches

		:param str cfg_path:
			Path to the configuration file without any powerline configuration 
			directory or ``.json`` suffix.
		:param str cfg_type:
			Configuration type. May be one of ``main`` (for ``config.json`` 
			file), ``colors``, ``colorscheme``, ``theme``.

		:return: dictionary with loaded configuration.
		'''
		return load_config(
			cfg_path,
			self.find_config_files,
			self.config_loader,
			self.cr_callbacks[cfg_type]
		)

	def _purge_configs(self, cfg_type):
		function = self.cr_callbacks[cfg_type]
		self.config_loader.unregister_functions(set((function,)))
		self.config_loader.unregister_missing(set(((self.find_config_files, function),)))

	def load_main_config(self):
		'''Get top-level configuration.

		:return: dictionary with :ref:`top-level configuration <config-main>`.
		'''
		return self.load_config('config', 'main')

	def _load_hierarhical_config(self, cfg_type, levels, ignore_levels):
		'''Load and merge multiple configuration files

		:param str cfg_type:
			Type of the loaded configuration files (e.g. ``colorscheme``, 
			``theme``).
		:param list levels:
			Configuration names resembling levels in hierarchy, sorted by 
			priority. Configuration file names with higher priority should go 
			last.
		:param set ignore_levels:
			If only files listed in this variable are present then configuration 
			file is considered not loaded: at least one file on the level not 
			listed in this variable must be present.
		'''
		config = {}
		loaded = 0
		exceptions = []
		for i, cfg_path in enumerate(levels):
			try:
				lvl_config = self.load_config(cfg_path, cfg_type)
			except IOError as e:
				if sys.version_info < (3,):
					tb = sys.exc_info()[2]
					exceptions.append((e, tb))
				else:
					exceptions.append(e)
			else:
				if i not in ignore_levels:
					loaded += 1
				mergedicts(config, lvl_config)
		if not loaded:
			for exception in exceptions:
				if type(exception) is tuple:
					e = exception[0]
				else:
					e = exception
				self.exception('Failed to load %s: {0}' % cfg_type, e, exception=exception)
			raise e
		return config

	def load_colorscheme_config(self, name):
		'''Get colorscheme.

		:param str name:
			Name of the colorscheme to load.

		:return: dictionary with :ref:`colorscheme configuration <config-colorschemes>`.
		'''
		levels = (
			os.path.join('colorschemes', name),
			os.path.join('colorschemes', self.ext, '__main__'),
			os.path.join('colorschemes', self.ext, name),
		)
		return self._load_hierarhical_config('colorscheme', levels, (1,))

	def load_theme_config(self, name):
		'''Get theme configuration.

		:param str name:
			Name of the theme to load.

		:return: dictionary with :ref:`theme configuration <config-themes>`
		'''
		levels = self.theme_levels + (
			os.path.join('themes', self.ext, name),
		)
		return self._load_hierarhical_config('theme', levels, (0, 1,))

	def load_colors_config(self):
		'''Get colorscheme.

		:return: dictionary with :ref:`colors configuration <config-colors>`.
		'''
		return self.load_config('colors', 'colors')

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
			exc = e
			try:
				self.exception('Failed to render: {0}', str(e))
			except Exception as e:
				exc = e
			ret = FailedUnicode(safe_unicode(exc))
			if kwargs.get('output_width', False):
				ret = ret, len(ret)
			return ret

	def render_above_lines(self, *args, **kwargs):
		'''Like .render(), but for ``self.renderer.render_above_lines()``
		'''
		try:
			self.update_renderer()
			for line in self.renderer.render_above_lines(*args, **kwargs):
				yield line
		except Exception as e:
			exc = e
			try:
				self.exception('Failed to render: {0}', str(e))
			except Exception as e:
				exc = e
			yield FailedUnicode(safe_unicode(exc))

	def setup(self, *args, **kwargs):
		'''Setup the environment to use powerline.

		Must not be overridden by subclasses. This one only saves setup 
		arguments for :py:meth:`reload` method and calls :py:meth:`do_setup`.
		'''
		self.shutdown_event.clear()
		self.setup_args = args
		self.setup_kwargs.update(kwargs)
		self.do_setup(*args, **kwargs)

	@staticmethod
	def do_setup():
		'''Function that does initialization

		Should be overridden by subclasses. May accept any number of regular or 
		keyword arguments.
		'''
		pass

	def reload(self):
		'''Reload powerline after update.

		Should handle most (but not all) powerline updates.

		Purges out all powerline modules and modules imported by powerline for 
		segment and matcher functions. Requires defining ``setup`` function that 
		updates reference to main powerline object.

		.. warning::
			Not guaranteed to work properly, use it at your own risk. It 
			may break your python code.
		'''
		import sys
		modules = self.imported_modules | set((module for module in sys.modules if module.startswith('powerline')))
		modules_holder = []
		for module in modules:
			try:
				# Needs to hold module to prevent garbage collecting until they 
				# are all reloaded.
				modules_holder.append(sys.modules.pop(module))
			except KeyError:
				pass
		PowerlineClass = getattr(__import__(self.__module__, fromlist=(self.__class__.__name__,)), self.__class__.__name__)
		self.shutdown(set_event=True)
		init_args, init_kwargs = self.init_args
		powerline = PowerlineClass(*init_args, **init_kwargs)
		powerline.setup(*self.setup_args, **self.setup_kwargs)

	def shutdown(self, set_event=True):
		'''Shut down all background threads.

		:param bool set_event:
			Set ``shutdown_event`` and call ``renderer.shutdown`` which should 
			shut down all threads. Set it to False unless you are exiting an 
			application.

			If set to False this does nothing more then resolving reference 
			cycle ``powerline → config_loader → bound methods → powerline`` by 
			unsubscribing from config_loader events.
		'''
		if set_event:
			self.shutdown_event.set()
			try:
				self.renderer.shutdown()
			except AttributeError:
				pass
		functions = tuple(self.cr_callbacks.values())
		self.config_loader.unregister_functions(set(functions))
		self.config_loader.unregister_missing(set(((self.find_config_files, function) for function in functions)))

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.shutdown()

	def exception(self, msg, *args, **kwargs):
		if 'prefix' not in kwargs:
			kwargs['prefix'] = 'powerline'
		exception = kwargs.pop('exception', None)
		pl = getattr(self, 'pl', None) or get_fallback_logger(self.default_log_stream)
		if exception:
			try:
				reraise(exception)
			except Exception:
				return pl.exception(msg, *args, **kwargs)
		return pl.exception(msg, *args, **kwargs)
