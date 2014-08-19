# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import, division
import tests.vim as vim_module
from tests import TestCase
from tests.lib.config_mock import get_powerline, get_powerline_raw, swap_attributes
from functools import wraps
from copy import deepcopy
import sys
import os


def highlighted_string(s, group, **kwargs):
	ret = {
		'type': 'string',
		'contents': s,
		'highlight_group': [group],
	}
	ret.update(kwargs)
	return ret


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
			'vim': {
				'theme': 'default',
				'colorscheme': 'default',
			},
		},
	},
	'colors': {
		'colors': {
			'col1': 1,
			'col2': 2,
			'col3': 3,
			'col4': 4,
			'col5': 5,
			'col6': 6,
			'col7': 7,
			'col8': 8,
			'col9': 9,
			'col10': 10,
			'col11': 11,
			'col12': 12,
		},
		'gradients': {
		},
	},
	'colorschemes/test/__main__': {
		'groups': {
			'm1': 'g1',
			'm2': 'g3',
			'm3': {'fg': 'col11', 'bg': 'col12', 'attr': []},
		}
	},
	'colorschemes/default': {
		'groups': {
			'g1': {'fg': 'col5', 'bg': 'col6', 'attr': []},
			'g2': {'fg': 'col7', 'bg': 'col8', 'attr': []},
			'g3': {'fg': 'col9', 'bg': 'col10', 'attr': []},
		}
	},
	'colorschemes/test/default': {
		'groups': {
			'str1': {'fg': 'col1', 'bg': 'col2', 'attr': ['bold']},
			'str2': {'fg': 'col3', 'bg': 'col4', 'attr': ['underline']},
			'd1': 'g2',
			'd2': 'm2',
			'd3': 'm3',
		},
	},
	'colorschemes/vim/default': {
		'groups': {
			'environment': {'fg': 'col3', 'bg': 'col4', 'attr': ['underline']},
		},
	},
	'themes/test/default': {
		'segments': {
			'left': [
				highlighted_string('s', 'str1', width='auto'),
				highlighted_string('g', 'str2'),
			],
			'right': [
				highlighted_string('f', 'str2', width='auto', align='right'),
			],
		},
	},
	'themes/powerline': {
		'dividers': {
			'left': {
				'hard': '>>',
				'soft': '>',
			},
			'right': {
				'hard': '<<',
				'soft': '<',
			},
		},
		'spaces': 0,
	},
	'themes/test/__main__': {
		'dividers': {
			'right': {
				'soft': '|',
			},
		},
	},
	'themes/vim/default': {
		'default_module': 'powerline.segments.common',
		'segments': {
			'left': [
				{
					'name': 'environment',
					'args': {
						'variable': 'TEST',
					},
				},
			],
		},
	},
}


def with_new_config(func):
	@wraps(func)
	def f(self):
		return func(self, deepcopy(config))
	return f


def add_args(func):
	@wraps(func)
	def f(self):
		new_config = deepcopy(config)
		with get_powerline(new_config, run_once=True, simpler_renderer=True) as p:
			func(self, p, new_config)
	return f


class TestRender(TestCase):
	def assertRenderEqual(self, p, output, **kwargs):
		self.assertEqual(p.render(**kwargs).replace(' ', ' '), output)

	def assertRenderLinesEqual(self, p, output, **kwargs):
		self.assertEqual([l.replace(' ', ' ') for l in p.render_above_lines(**kwargs)], output)


class TestLines(TestRender):
	@add_args
	def test_without_above(self, p, config):
		self.assertRenderEqual(p, '{121} s{24}>>{344}g{34}>{34}|{344}f {--}')
		self.assertRenderEqual(p, '{121} s {24}>>{344}g{34}>{34}|{344}f {--}', width=10)
		# self.assertRenderEqual(p, '{121} s {24}>>{344}g{34}>{34}|{344} f {--}', width=11)
		self.assertEqual(list(p.render_above_lines()), [])

	@with_new_config
	def test_with_above(self, config):
		old_segments = deepcopy(config['themes/test/default']['segments'])
		config['themes/test/default']['segments']['above'] = [old_segments]
		with get_powerline(config, run_once=True, simpler_renderer=True) as p:
			self.assertRenderLinesEqual(p, [
				'{121} s{24}>>{344}g{34}>{34}|{344}f {--}',
			])
			self.assertRenderLinesEqual(p, [
				'{121} s {24}>>{344}g{34}>{34}|{344}f {--}',
			], width=10)

		config['themes/test/default']['segments']['above'] = [old_segments] * 2
		with get_powerline(config, run_once=True, simpler_renderer=True) as p:
			self.assertRenderLinesEqual(p, [
				'{121} s{24}>>{344}g{34}>{34}|{344}f {--}',
				'{121} s{24}>>{344}g{34}>{34}|{344}f {--}',
			])
			self.assertRenderLinesEqual(p, [
				'{121} s {24}>>{344}g{34}>{34}|{344}f {--}',
				'{121} s {24}>>{344}g{34}>{34}|{344}f {--}',
			], width=10)


class TestSegments(TestRender):
	@add_args
	def test_display(self, p, config):
		config['themes/test/default']['segments']['left'][0]['display'] = False
		config['themes/test/default']['segments']['left'][1]['display'] = True
		config['themes/test/default']['segments']['right'][0]['display'] = False
		self.assertRenderEqual(p, '{344} g{4-}>>{--}')


class TestColorschemesHierarchy(TestRender):
	@add_args
	def test_group_redirects(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('a', 'd1', draw_hard_divider=False),
				highlighted_string('b', 'd2', draw_hard_divider=False),
				highlighted_string('c', 'd3', draw_hard_divider=False),
				highlighted_string('A', 'm1', draw_hard_divider=False),
				highlighted_string('B', 'm2', draw_hard_divider=False),
				highlighted_string('C', 'm3', draw_hard_divider=False),
				highlighted_string('1', 'g1', draw_hard_divider=False),
				highlighted_string('2', 'g2', draw_hard_divider=False),
				highlighted_string('3', 'g3', draw_hard_divider=False),
			],
			'right': [],
		}
		self.assertRenderEqual(p, '{78} a{910}b{1112}c{56}A{910}B{1112}C{56}1{78}2{910}3{--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_group_redirects_no_main(self, p, config):
		del config['colorschemes/test/__main__']
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('a', 'd1', draw_hard_divider=False),
				highlighted_string('1', 'g1', draw_hard_divider=False),
				highlighted_string('2', 'g2', draw_hard_divider=False),
				highlighted_string('3', 'g3', draw_hard_divider=False),
			],
			'right': [],
		}
		self.assertRenderEqual(p, '{78} a{56}1{78}2{910}3{--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_group_redirects_no_top_default(self, p, config):
		del config['colorschemes/default']
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('c', 'd3', draw_soft_divider=False),
				highlighted_string('C', 'm3', draw_hard_divider=False),
			],
			'right': [],
		}
		self.assertRenderEqual(p, '{1112} c{1112}C{--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_group_redirects_no_test_default(self, p, config):
		del config['colorschemes/test/default']
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('A', 'm1', draw_hard_divider=False),
				highlighted_string('B', 'm2', draw_hard_divider=False),
				highlighted_string('C', 'm3', draw_hard_divider=False),
				highlighted_string('1', 'g1', draw_hard_divider=False),
				highlighted_string('2', 'g2', draw_hard_divider=False),
				highlighted_string('3', 'g3', draw_hard_divider=False),
			],
			'right': [],
		}
		self.assertRenderEqual(p, '{56} A{910}B{1112}C{56}1{78}2{910}3{--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_group_redirects_only_main(self, p, config):
		del config['colorschemes/default']
		del config['colorschemes/test/default']
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('C', 'm3', draw_hard_divider=False),
			],
			'right': [],
		}
		# Powerline is not able to work without default colorscheme 
		# somewhere, thus it will output error string
		self.assertRenderEqual(p, 'colorschemes/test/default')
		self.assertEqual(p.logger._pop_msgs(), [
			'exception:test:powerline:Failed to load colorscheme: colorschemes/default',
			'exception:test:powerline:Failed to load colorscheme: colorschemes/test/default',
			'exception:test:powerline:Failed to create renderer: colorschemes/test/default',
			'exception:test:powerline:Failed to render: colorschemes/test/default',
		])

	@add_args
	def test_group_redirects_only_top_default(self, p, config):
		del config['colorschemes/test/__main__']
		del config['colorschemes/test/default']
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('1', 'g1', draw_hard_divider=False),
				highlighted_string('2', 'g2', draw_hard_divider=False),
				highlighted_string('3', 'g3', draw_hard_divider=False),
			],
			'right': [],
		}
		self.assertRenderEqual(p, '{56} 1{78}2{910}3{--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_group_redirects_only_test_default(self, p, config):
		del config['colorschemes/default']
		del config['colorschemes/test/__main__']
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s', 'str1', draw_hard_divider=False),
			],
			'right': [],
		}
		self.assertRenderEqual(p, '{121} s{--}')
		self.assertEqual(p.logger._pop_msgs(), [])


class TestThemeHierarchy(TestRender):
	@add_args
	def test_hierarchy(self, p, config):
		self.assertRenderEqual(p, '{121} s{24}>>{344}g{34}>{34}|{344}f {--}')

	@add_args
	def test_no_main(self, p, config):
		del config['themes/test/__main__']
		self.assertRenderEqual(p, '{121} s{24}>>{344}g{34}>{34}<{344}f {--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_no_powerline(self, p, config):
		config['themes/test/__main__']['dividers'] = config['themes/powerline']['dividers']
		config['themes/test/__main__']['spaces'] = 1
		del config['themes/powerline']
		self.assertRenderEqual(p, '{121} s {24}>>{344}g {34}>{34}<{344} f {--}')
		self.assertEqual(p.logger._pop_msgs(), [])

	@add_args
	def test_no_default(self, p, config):
		del config['themes/test/default']
		self.assertRenderEqual(p, 'themes/test/default')
		self.assertEqual(p.logger._pop_msgs(), [
			'exception:test:powerline:Failed to load theme: themes/test/default',
			'exception:test:powerline:Failed to create renderer: themes/test/default',
			'exception:test:powerline:Failed to render: themes/test/default',
		])

	@add_args
	def test_only_default(self, p, config):
		config['themes/test/default']['dividers'] = config['themes/powerline']['dividers']
		config['themes/test/default']['spaces'] = 1
		del config['themes/test/__main__']
		del config['themes/powerline']
		self.assertRenderEqual(p, '{121} s {24}>>{344}g {34}>{34}<{344} f {--}')

	@add_args
	def test_only_main(self, p, config):
		del config['themes/test/default']
		del config['themes/powerline']
		self.assertRenderEqual(p, 'themes/test/default')
		self.assertEqual(p.logger._pop_msgs(), [
			'exception:test:powerline:Failed to load theme: themes/powerline',
			'exception:test:powerline:Failed to load theme: themes/test/default',
			'exception:test:powerline:Failed to create renderer: themes/test/default',
			'exception:test:powerline:Failed to render: themes/test/default',
		])

	@add_args
	def test_only_powerline(self, p, config):
		del config['themes/test/default']
		del config['themes/test/__main__']
		self.assertRenderEqual(p, 'themes/test/default')
		self.assertEqual(p.logger._pop_msgs(), [
			'exception:test:powerline:Failed to load theme: themes/test/__main__',
			'exception:test:powerline:Failed to load theme: themes/test/default',
			'exception:test:powerline:Failed to create renderer: themes/test/default',
			'exception:test:powerline:Failed to render: themes/test/default',
		])

	@add_args
	def test_nothing(self, p, config):
		del config['themes/test/default']
		del config['themes/powerline']
		del config['themes/test/__main__']
		self.assertRenderEqual(p, 'themes/test/default')
		self.assertEqual(p.logger._pop_msgs(), [
			'exception:test:powerline:Failed to load theme: themes/powerline',
			'exception:test:powerline:Failed to load theme: themes/test/__main__',
			'exception:test:powerline:Failed to load theme: themes/test/default',
			'exception:test:powerline:Failed to create renderer: themes/test/default',
			'exception:test:powerline:Failed to render: themes/test/default',
		])


class TestVim(TestCase):
	def test_environ_update(self):
		# Regression test: test that segment obtains environment from vim, not 
		# from os.environ.
		from powerline.vim import VimPowerline
		import powerline as powerline_module
		import vim
		vim.vars['powerline_config_path'] = '/'
		with swap_attributes(config, powerline_module):
			with vim_module._with('environ', TEST='abc'):
				with get_powerline_raw(config, VimPowerline) as powerline:
					window = vim_module.current.window
					window_id = 1
					winnr = window.number
					self.assertEqual(powerline.render(window, window_id, winnr), '%#Pl_3_8404992_4_192_underline#\xa0abc%#Pl_4_192_NONE_None_NONE#>>')
					vim_module._environ['TEST'] = 'def'
					self.assertEqual(powerline.render(window, window_id, winnr), '%#Pl_3_8404992_4_192_underline#\xa0def%#Pl_4_192_NONE_None_NONE#>>')

	def test_local_themes(self):
		# Regression test: VimPowerline.add_local_theme did not work properly.
		from powerline.vim import VimPowerline
		import powerline as powerline_module
		import vim
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, VimPowerline) as powerline:
				powerline.add_local_theme('tests.matchers.always_true', {
					'segment_data': {
						'foo': {
							'contents': '“bar”'
						}
					},
					'segments': {
						'left': [
							{
								'type': 'string',
								'name': 'foo',
								'highlight_group': ['g1']
							}
						]
					}
				})
				window = vim_module.current.window
				window_id = 1
				winnr = window.number
				self.assertEqual(powerline.render(window, window_id, winnr), '%#Pl_5_12583104_6_32896_NONE#\xa0\u201cbar\u201d%#Pl_6_32896_NONE_None_NONE#>>')


def setUpModule():
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'path')))


def tearDownModule():
	sys.path.pop(0)


if __name__ == '__main__':
	from tests import main
	main()
