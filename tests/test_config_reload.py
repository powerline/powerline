# vim:fileencoding=utf-8:noet

import powerline as powerline_module
import time
from powerline.renderer import Renderer
from tests import TestCase
from tests.lib import replace_item
from copy import deepcopy
from threading import Lock


class Watcher(object):
	events = set()

	def watch(self, file):
		pass

	def __call__(self, file):
		if file in self.events:
			self.events.remove(file)
			return True
		return False

	def _add(self, file):
		self.events.add(file)


class Logger(object):
	def __init__(self):
		self.messages = []
		self.lock = Lock()

	def _add_msg(self, msg):
		with self.lock:
			self.messages.append(msg)

	def _pop_msgs(self):
		with self.lock:
			r = self.messages
			self.messages = []
		return r

	def __getattr__(self, attr):
		return self._add_msg


config = {
	'config': {
		'common': {
			'dividers': {
			},
			'spaces': 0,
		},
		'ext': {
			'test': {
				'theme': 'default',
				'colorscheme': 'default',
			},
		},
	},
	'colors': {
		'colors': {
		},
		'gradients': {
		},
	},
	'colorschemes/test/default': {
		'groups': {
		},
	},
	'themes/test/default': {
		'segments': {
		},
	},
}


access_log = []
access_lock = Lock()


def load_json_config(config_file_path, *args, **kwargs):
	global access_log
	with access_lock:
		access_log.append(config_file_path)
	try:
		return deepcopy(config[config_file_path])
	except KeyError:
		raise IOError(config_file_path)


def find_config_file(search_paths, config_file):
	return config_file


class SimpleRenderer(Renderer):
	def hlstyle(self, fg=None, bg=None, attr=None):
		return '<{fg} {bg} {attr}>'.format(fg=fg, bg=bg, attr=attr)


class TestPowerline(powerline_module.Powerline):
	@staticmethod
	def get_local_themes(local_themes):
		return local_themes


renderer = SimpleRenderer


def get_powerline(**kwargs):
	return TestPowerline(ext='test', renderer_module='tests.test_config_reload', interval=0, logger=Logger(), **kwargs)


# Minimum sleep time on my system is 0.000001, otherwise it fails to update 
# config
# This sleep time is 100 times bigger
def sleep(interval=0.0001):
	time.sleep(interval)


def add_watcher_events(*args):
	Watcher.events.update(args)
	sleep()


class TestConfigReload(TestCase):
	def assertAccessEvents(self, *args):
		global access_log
		with access_lock:
			self.assertEqual(set(access_log), set(args))
			access_log = []

	def test_noreload(self):
		with get_powerline(run_once=True) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				config['config']['common']['spaces'] = 1
				add_watcher_events('config')
				# When running once thread should not start
				self.assertAccessEvents()
				self.assertEqual(p.render(), '<None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

	def test_reload_main(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertEqual(p.render(), '<None None None>')
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')

				config['config']['common']['spaces'] = 1
				add_watcher_events('config')
				self.assertAccessEvents('config')
				self.assertEqual(p.render(), '<None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['theme'] = 'new'
				add_watcher_events('config')
				self.assertAccessEvents('config', 'themes/test/new')
				self.assertEqual(p.render(), '<None None None>')
				# It should normally handle file missing error
				self.assertEqual(p.logger._pop_msgs(), ['test:Failed to create renderer: themes/test/new'])

				config['config']['ext']['test']['theme'] = 'default'
				add_watcher_events('config')
				self.assertAccessEvents('config', 'themes/test/default')
				self.assertEqual(p.render(), '<None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['colorscheme'] = 'new'
				add_watcher_events('config')
				self.assertAccessEvents('config', 'colorschemes/test/new')
				self.assertEqual(p.render(), '<None None None>')
				# It should normally handle file missing error
				self.assertEqual(p.logger._pop_msgs(), ['test:Failed to create renderer: colorschemes/test/new'])

				config['config']['ext']['test']['colorscheme'] = 'default'
				add_watcher_events('config')
				self.assertAccessEvents('config', 'colorschemes/test/default')
				self.assertEqual(p.render(), '<None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				self.assertEqual(p.renderer.local_themes, None)
				config['config']['ext']['test']['local_themes'] = 'something'
				add_watcher_events('config')
				self.assertAccessEvents('config')
				self.assertEqual(p.render(), '<None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
				self.assertEqual(p.renderer.local_themes, 'something')


replaces = {
	'watcher': Watcher(),
	'load_json_config': load_json_config,
	'find_config_file': find_config_file,
}


def swap_attributes():
	global replaces
	for attr, val in replaces.items():
		old_val = getattr(powerline_module, attr)
		setattr(powerline_module, attr, val)
		replaces[attr] = old_val


tearDownModule = setUpModule = swap_attributes


if __name__ == '__main__':
	from tests import main
	main()
