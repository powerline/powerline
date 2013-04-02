# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals
import powerline as powerline_module
import time
from powerline.renderer import Renderer
from tests import TestCase
from tests.lib import replace_item
from copy import deepcopy
from threading import Lock


class Watcher(object):
	events = set()
	lock = Lock()

	def watch(self, file):
		pass

	def __call__(self, file):
		if file in self.events:
			with self.lock:
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
				"left": {
					"hard": ">>",
					"soft": ">",
				},
				"right": {
					"hard": "<<",
					"soft": "<",
				},
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
			"col1": 1,
			"col2": 2,
			"col3": 3,
			"col4": 4,
		},
		'gradients': {
		},
	},
	'colorschemes/test/default': {
		'groups': {
			"str1": {"fg": "col1", "bg": "col2", "attr": ["bold"]},
			"str2": {"fg": "col3", "bg": "col4", "attr": ["underline"]},
		},
	},
	'colorschemes/test/2': {
		'groups': {
			"str1": {"fg": "col2", "bg": "col3", "attr": ["bold"]},
			"str2": {"fg": "col1", "bg": "col4", "attr": ["underline"]},
		},
	},
	'themes/test/default': {
		'segments': {
			"left": [
				{
					"type": "string",
					"contents": "s",
					"highlight_group": ["str1"],
				},
				{
					"type": "string",
					"contents": "g",
					"highlight_group": ["str2"],
				},
			],
			"right": [
			],
		},
	},
	'themes/test/2': {
		'segments': {
			"left": [
				{
					"type": "string",
					"contents": "t",
					"highlight_group": ["str1"],
				},
				{
					"type": "string",
					"contents": "b",
					"highlight_group": ["str2"],
				},
			],
			"right": [
			],
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
	if config_file.endswith('raise') and config_file not in config:
		raise IOError('fcf:' + config_file)
	return config_file


class SimpleRenderer(Renderer):
	def hlstyle(self, fg=None, bg=None, attr=None):
		return '<{fg} {bg} {attr}>'.format(fg=fg and fg[0], bg=bg and bg[0], attr=attr)


class TestPowerline(powerline_module.Powerline):
	_created = False

	@staticmethod
	def get_local_themes(local_themes):
		return local_themes

	def create_renderer(self, *args, **kwargs):
		try:
			r = super(TestPowerline, self).create_renderer(*args, **kwargs)
		finally:
			self._created = True
		return r

	def _created_renderer(self):
		if self._created:
			self._created = False
			return True
		return False


renderer = SimpleRenderer


def get_powerline(**kwargs):
	return TestPowerline(
		ext='test',
		renderer_module='tests.test_config_reload',
		interval=0,
		logger=Logger(),
		watcher=Watcher(),
		**kwargs
	)


def sleep(interval):
	time.sleep(interval)


def add_watcher_events(p, *args, **kwargs):
	p._created_renderer()
	p.watcher._reset(args)
	while not p._created_renderer():
		sleep(kwargs.get('interval', 0.000001))
		if not kwargs.get('wait', True):
			return


class TestConfigReload(TestCase):
	def assertAccessEvents(self, *args):
		global access_log
		with access_lock:
			self.assertEqual(set(access_log), set(args))
			access_log = []

	def test_noreload(self):
		with get_powerline(run_once=True) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				config['config']['common']['spaces'] = 1
				add_watcher_events(p, 'config', wait=False, interval=0.05)
				# When running once thread should not start
				self.assertAccessEvents()
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
		# Without the following assertion test_reload_colors may fail for 
		# unknown reason (with AssertionError telling about “config” accessed 
		# one more time then needed)
		self.assertAccessEvents()

	def test_reload_main(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')

				config['config']['common']['spaces'] = 1
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['theme'] = 'nonexistent'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config', 'themes/test/nonexistent')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				# It should normally handle file missing error
				self.assertEqual(p.logger._pop_msgs(), ['test:Failed to create renderer: themes/test/nonexistent'])

				config['config']['ext']['test']['theme'] = 'default'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['colorscheme'] = 'nonexistent'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config', 'colorschemes/test/nonexistent')
				self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
				# It should normally handle file missing error
				self.assertEqual(p.logger._pop_msgs(), ['test:Failed to create renderer: colorschemes/test/nonexistent'])

				config['config']['ext']['test']['colorscheme'] = '2'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config', 'colorschemes/test/2')
				self.assertEqual(p.render(), '<2 3 1> s <3 4 False>>><1 4 4>g <4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				config['config']['ext']['test']['theme'] = '2'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config', 'themes/test/2')
				self.assertEqual(p.render(), '<2 3 1> t <3 4 False>>><1 4 4>b <4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])

				self.assertEqual(p.renderer.local_themes, None)
				config['config']['ext']['test']['local_themes'] = 'something'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config')
				self.assertEqual(p.render(), '<2 3 1> t <3 4 False>>><1 4 4>b <4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
				self.assertEqual(p.renderer.local_themes, 'something')
		self.assertAccessEvents()

	def test_reload_unexistent(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')

				config['config']['ext']['test']['colorscheme'] = 'nonexistentraise'
				add_watcher_events(p, 'config')
				self.assertAccessEvents('config')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), ['test:Failed to create renderer: fcf:colorschemes/test/nonexistentraise'])

				config['colorschemes/test/nonexistentraise'] = {
					'groups': {
						"str1": {"fg": "col1", "bg": "col3", "attr": ["bold"]},
						"str2": {"fg": "col2", "bg": "col4", "attr": ["underline"]},
					},
				}
				while not p._created_renderer():
					sleep(0.000001)
				self.assertAccessEvents('colorschemes/test/nonexistentraise')
				self.assertEqual(p.render(), '<1 3 1> s<3 4 False>>><2 4 4>g<4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
		self.assertAccessEvents()

	def test_reload_colors(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')

				config['colors']['colors']['col1'] = 5
				add_watcher_events(p, 'colors')
				self.assertAccessEvents('colors')
				self.assertEqual(p.render(), '<5 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
		self.assertAccessEvents()

	def test_reload_colorscheme(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')

				config['colorschemes/test/default']['groups']['str1']['bg'] = 'col3'
				add_watcher_events(p, 'colorschemes/test/default')
				self.assertAccessEvents('colorschemes/test/default')
				self.assertEqual(p.render(), '<1 3 1> s<3 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
		self.assertAccessEvents()

	def test_reload_theme(self):
		with get_powerline(run_once=False) as p:
			with replace_item(globals(), 'config', deepcopy(config)):
				self.assertAccessEvents('config', 'colors', 'colorschemes/test/default', 'themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')

				config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
				add_watcher_events(p, 'themes/test/default')
				self.assertAccessEvents('themes/test/default')
				self.assertEqual(p.render(), '<1 2 1> col3<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
				self.assertEqual(p.logger._pop_msgs(), [])
		self.assertAccessEvents()


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
