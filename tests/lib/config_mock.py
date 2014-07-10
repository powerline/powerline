# vim:fileencoding=utf-8:noet
from threading import Lock
from powerline.renderer import Renderer
from powerline.lib.config import ConfigLoader
from powerline import Powerline
from copy import deepcopy
from time import sleep
from functools import wraps


access_log = []
access_lock = Lock()


def load_json_config(config_file_path, *args, **kwargs):
	global access_log
	with access_lock:
		access_log.append(config_file_path)
	try:
		return deepcopy(config_container['config'][config_file_path])
	except KeyError:
		raise IOError(config_file_path)


def _find_config_file(config, search_paths, config_file):
	if config_file.endswith('raise') and config_file not in config:
		raise IOError('fcf:' + config_file)
	return config_file


def pop_events():
	global access_log
	with access_lock:
		r = access_log[:]
		access_log = []
	return r


def log_call(func):
	@wraps(func)
	def ret(self, *args, **kwargs):
		self._calls.append((func.__name__, args, kwargs))
		return func(self, *args, **kwargs)
	return ret


class Watcher(object):
	events = set()
	lock = Lock()

	def __init__(self):
		self._calls = []

	@log_call
	def watch(self, file):
		pass

	@log_call
	def __call__(self, file):
		with self.lock:
			if file in self.events:
				self.events.remove(file)
				return True
		return False

	def _reset(self, files):
		with self.lock:
			self.events.clear()
			self.events.update(files)

	@log_call
	def unsubscribe(self):
		pass


class Logger(object):
	def __init__(self):
		self.messages = []
		self.lock = Lock()

	def _add_msg(self, attr, msg):
		with self.lock:
			self.messages.append(attr + ':' + msg)

	def _pop_msgs(self):
		with self.lock:
			r = self.messages
			self.messages = []
		return r

	def __getattr__(self, attr):
		return lambda *args, **kwargs: self._add_msg(attr, *args, **kwargs)


class SimpleRenderer(Renderer):
	def hlstyle(self, fg=None, bg=None, attr=None):
		return '<{fg} {bg} {attr}>'.format(fg=fg and fg[0], bg=bg and bg[0], attr=attr)


class EvenSimplerRenderer(Renderer):
	def hlstyle(self, fg=None, bg=None, attr=None):
		return '{{{fg}{bg}{attr}}}'.format(
			fg=fg and fg[0] or '-',
			bg=bg and bg[0] or '-',
			attr=attr if attr else '',
		)


class TestPowerline(Powerline):
	_created = False

	@staticmethod
	def get_local_themes(local_themes):
		return local_themes

	def _will_create_renderer(self):
		return self.cr_kwargs


renderer = SimpleRenderer


def get_powerline(**kwargs):
	return get_powerline_raw(
		TestPowerline,
		ext='test',
		renderer_module='tests.lib.config_mock',
		logger=Logger(),
		**kwargs
	)


def get_powerline_raw(PowerlineClass, **kwargs):
	global renderer
	watcher = Watcher()
	if kwargs.pop('simpler_renderer', False):
		renderer = EvenSimplerRenderer
	else:
		renderer = SimpleRenderer
	pl = PowerlineClass(
		config_loader=ConfigLoader(
			load=load_json_config,
			watcher=watcher,
			watcher_type='test',
			run_once=kwargs.get('run_once')
		),
		**kwargs
	)
	pl._watcher = watcher
	return pl


config_container = None


def swap_attributes(cfg_container, powerline_module, replaces):
	global config_container
	config_container = cfg_container
	if not replaces:
		replaces = {
			'_find_config_file': lambda *args: _find_config_file(config_container['config'], *args),
		}
	for attr, val in replaces.items():
		old_val = getattr(powerline_module, attr)
		setattr(powerline_module, attr, val)
		replaces[attr] = old_val
	return replaces


def add_watcher_events(p, *args, **kwargs):
	p._watcher._reset(args)
	while not p._will_create_renderer():
		sleep(kwargs.get('interval', 0.1))
		if not kwargs.get('wait', True):
			return
