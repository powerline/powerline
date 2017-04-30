# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from time import sleep
from copy import deepcopy
from functools import wraps

from tests.modules import TestCase
from tests.modules.lib.config_mock import get_powerline, add_watcher_events, UT


config = {
	'config': {
		'common': {
			'interval': 0,
			'watcher': 'test',
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
			'str1': {'fg': 'col1', 'bg': 'col2', 'attrs': ['bold']},
			'str2': {'fg': 'col3', 'bg': 'col4', 'attrs': ['underline']},
		},
	},
	'colorschemes/test/2': {
		'groups': {
			'str1': {'fg': 'col2', 'bg': 'col3', 'attrs': ['bold']},
			'str2': {'fg': 'col1', 'bg': 'col4', 'attrs': ['underline']},
		},
	},
	'themes/test/default': {
		'segments': {
			"left": [
				{
					"type": "string",
					"contents": "s",
					"highlight_groups": ["str1"],
				},
				{
					"type": "string",
					"contents": "g",
					"highlight_groups": ["str2"],
				},
			],
			"right": [
			],
		},
	},
	'themes/' + UT: {
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
	'themes/other': {
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
		'spaces': 1,
	},
	'themes/test/2': {
		'segments': {
			"left": [
				{
					"type": "string",
					"contents": "t",
					"highlight_groups": ["str1"],
				},
				{
					"type": "string",
					"contents": "b",
					"highlight_groups": ["str2"],
				},
			],
			"right": [
			],
		},
	},
}


def with_new_config(func):
	@wraps(func)
	def f(self):
		return func(self, deepcopy(config))
	return f


class TestConfigReload(TestCase):
	def assertAccessEvents(self, p, *args):
		events = set()
		for event in args:
			if ':' not in event:
				events.add('check:' + event)
				events.add('load:' + event)
			else:
				events.add(event)
		self.assertEqual(set(p._pop_events()), events)

	@with_new_config
	def test_noreload(self, config):
		with get_powerline(config, run_once=True) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')
			config['config']['common']['spaces'] = 1
			add_watcher_events(p, 'config', wait=False, interval=0.05)
			# When running once thread should not start
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p)
			self.assertEqual(p.logger._pop_msgs(), [])

	@with_new_config
	def test_reload_main(self, config):
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['config']['common']['default_top_theme'] = 'other'
			add_watcher_events(p, 'config')
			p.render()
			self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'themes/other', 'check:themes/test/__main__', 'themes/test/default')
			self.assertEqual(p.logger._pop_msgs(), [])

			config['config']['ext']['test']['theme'] = 'nonexistent'
			add_watcher_events(p, 'config')
			self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'check:themes/test/nonexistent', 'themes/other', 'check:themes/test/__main__')
			# It should normally handle file missing error
			self.assertEqual(p.logger._pop_msgs(), [
				'exception:test:powerline:Failed to load theme: themes/test/__main__',
				'exception:test:powerline:Failed to load theme: themes/test/nonexistent',
				'exception:test:powerline:Failed to create renderer: themes/test/nonexistent'
			])

			config['config']['ext']['test']['theme'] = 'default'
			add_watcher_events(p, 'config')
			self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'themes/test/default', 'themes/other', 'check:themes/test/__main__')
			self.assertEqual(p.logger._pop_msgs(), [])

			config['config']['ext']['test']['colorscheme'] = 'nonexistent'
			add_watcher_events(p, 'config')
			self.assertEqual(p.render(), '<1 2 1> s <2 4 False>>><3 4 4>g <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'check:colorschemes/nonexistent', 'check:colorschemes/test/__main__', 'check:colorschemes/test/nonexistent')
			# It should normally handle file missing error
			self.assertEqual(p.logger._pop_msgs(), [
				'exception:test:powerline:Failed to load colorscheme: colorschemes/nonexistent',
				'exception:test:powerline:Failed to load colorscheme: colorschemes/test/__main__',
				'exception:test:powerline:Failed to load colorscheme: colorschemes/test/nonexistent',
				'exception:test:powerline:Failed to create renderer: colorschemes/test/nonexistent'
			])

			config['config']['ext']['test']['colorscheme'] = '2'
			add_watcher_events(p, 'config')
			self.assertEqual(p.render(), '<2 3 1> s <3 4 False>>><1 4 4>g <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'check:colorschemes/2', 'check:colorschemes/test/__main__', 'colorschemes/test/2')
			self.assertEqual(p.logger._pop_msgs(), [])

			config['config']['ext']['test']['theme'] = '2'
			add_watcher_events(p, 'config')
			self.assertEqual(p.render(), '<2 3 1> t <3 4 False>>><1 4 4>b <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'themes/test/2', 'themes/other', 'check:themes/test/__main__')
			self.assertEqual(p.logger._pop_msgs(), [])

			self.assertEqual(p.renderer.local_themes, None)
			config['config']['ext']['test']['local_themes'] = 'something'
			add_watcher_events(p, 'config')
			self.assertEqual(p.render(), '<2 3 1> t <3 4 False>>><1 4 4>b <4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config')
			self.assertEqual(p.logger._pop_msgs(), [])
			self.assertEqual(p.renderer.local_themes, 'something')

	@with_new_config
	def test_reload_unexistent(self, config):
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['config']['ext']['test']['colorscheme'] = 'nonexistentraise'
			add_watcher_events(p, 'config')
			# It may appear that p.logger._pop_msgs() is called after given 
			# exception is added to the mesagges, but before config_loader 
			# exception was added (this one: 
			# “exception:test:config_loader:Error while running condition 
			# function for key colorschemes/test/nonexistentraise: 
			# fcf:colorschemes/test/nonexistentraise”).
			# sleep(0.1)
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			# For colorschemes/{test/,}*raise find_config_file raises 
			# IOError, but it does not do so for check:colorschemes/test/__main__, 
			# so powerline is trying to load this, but not other 
			# colorschemes/*
			self.assertAccessEvents(p, 'config', 'check:colorschemes/test/__main__', 'check:colorschemes/nonexistentraise', 'check:colorschemes/test/nonexistentraise')
			self.assertIn('exception:test:powerline:Failed to create renderer: fcf:colorschemes/test/nonexistentraise', p.logger._pop_msgs())

			config['colorschemes/nonexistentraise'] = {}
			config['colorschemes/test/nonexistentraise'] = {
				'groups': {
					'str1': {'fg': 'col1', 'bg': 'col3', 'attrs': ['bold']},
					'str2': {'fg': 'col2', 'bg': 'col4', 'attrs': ['underline']},
				},
			}
			while not p._will_create_renderer():
				sleep(0.1)
			self.assertEqual(p.render(), '<1 3 1> s<3 4 False>>><2 4 4>g<4 False False>>><None None None>')
			# Same as above
			self.assertAccessEvents(p, 'colorschemes/nonexistentraise', 'colorschemes/test/nonexistentraise', 'check:colorschemes/test/__main__')
			self.assertEqual(p.logger._pop_msgs(), [])

	@with_new_config
	def test_reload_colors(self, config):
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['colors']['colors']['col1'] = 5
			add_watcher_events(p, 'colors')
			self.assertEqual(p.render(), '<5 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'colors')
			self.assertEqual(p.logger._pop_msgs(), [])

	@with_new_config
	def test_reload_colorscheme(self, config):
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['colorschemes/test/default']['groups']['str1']['bg'] = 'col3'
			add_watcher_events(p, 'colorschemes/test/default')
			self.assertEqual(p.render(), '<1 3 1> s<3 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default')
			self.assertEqual(p.logger._pop_msgs(), [])

	@with_new_config
	def test_reload_theme(self, config):
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
			add_watcher_events(p, 'themes/test/default')
			self.assertEqual(p.render(), '<1 2 1> col3<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')
			self.assertEqual(p.logger._pop_msgs(), [])

	@with_new_config
	def test_reload_top_theme(self, config):
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['themes/' + UT]['dividers']['left']['hard'] = '|>'
			add_watcher_events(p, 'themes/' + UT)
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>|><3 4 4>g<4 False False>|><None None None>')
			self.assertAccessEvents(p, 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')
			self.assertEqual(p.logger._pop_msgs(), [])

	@with_new_config
	def test_reload_theme_main(self, config):
		config['config']['common']['interval'] = None
		with get_powerline(config, run_once=False) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
			add_watcher_events(p, 'themes/test/default', wait=False)
			self.assertEqual(p.render(), '<1 2 1> col3<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')
			self.assertEqual(p.logger._pop_msgs(), [])
			self.assertTrue(p._watcher._calls)

	@with_new_config
	def test_run_once_no_theme_reload(self, config):
		config['config']['common']['interval'] = None
		with get_powerline(config, run_once=True) as p:
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p, 'config', 'colors', 'check:colorschemes/default', 'check:colorschemes/test/__main__', 'colorschemes/test/default', 'themes/test/default', 'themes/' + UT, 'check:themes/test/__main__')

			config['themes/test/default']['segments']['left'][0]['contents'] = 'col3'
			add_watcher_events(p, 'themes/test/default', wait=False)
			self.assertEqual(p.render(), '<1 2 1> s<2 4 False>>><3 4 4>g<4 False False>>><None None None>')
			self.assertAccessEvents(p)
			self.assertEqual(p.logger._pop_msgs(), [])


if __name__ == '__main__':
	from tests.modules import main
	main()
