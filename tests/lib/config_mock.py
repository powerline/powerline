# vim:fileencoding=utf-8:noet
from threading import Lock
from powerline.renderer import Renderer
from powerline.lib.config import ConfigLoader
from powerline import Powerline
from copy import deepcopy


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


def find_config_file(config, search_paths, config_file):
	if config_file.endswith('raise') and config_file not in config:
		raise IOError('fcf:' + config_file)
	return config_file


def pop_events():
	global access_log
	with access_lock:
		r = access_log[:]
		access_log = []
	return r


class Watcher(object):
	events = set()
	lock = Lock()

	def watch(self, file):
		pass

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


class TestPowerline(Powerline):
	_created = False

	@staticmethod
	def get_local_themes(local_themes):
		return local_themes

	def _will_create_renderer(self):
		return self.create_renderer_kwargs


renderer = SimpleRenderer


def get_powerline(**kwargs):
	return TestPowerline(
		ext='test',
		renderer_module='tests.lib.config_mock',
		logger=Logger(),
		config_loader=ConfigLoader(load=load_json_config, watcher=Watcher()),
		**kwargs
	)


config_container = None


def swap_attributes(cfg_container, powerline_module, replaces):
	global config_container
	config_container = cfg_container
	if not replaces:
		replaces = {
			'find_config_file': lambda *args: find_config_file(config_container['config'], *args),
		}
	for attr, val in replaces.items():
		old_val = getattr(powerline_module, attr)
		setattr(powerline_module, attr, val)
		replaces[attr] = old_val
	return replaces
