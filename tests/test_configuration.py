# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import, division
import tests.vim as vim_module
import powerline as powerline_module
from tests import TestCase
from tests.lib import replace_item
from tests.lib.config_mock import swap_attributes, get_powerline
from tests.lib.config_mock import get_powerline_raw
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


def add_p_arg(func):
	@wraps(func)
	def f(self):
		with get_powerline(run_once=True, simpler_renderer=True) as p:
			func(self, p)
	return f


class TestRender(TestCase):
	def assertRenderEqual(self, p, output, **kwargs):
		self.assertEqual(p.render(**kwargs).replace(' ', ' '), output)

	def assertRenderLinesEqual(self, p, output, **kwargs):
		self.assertEqual([l.replace(' ', ' ') for l in p.render_above_lines(**kwargs)], output)


class TestLines(TestRender):
	@add_p_arg
	def test_without_above(self, p):
		self.assertRenderEqual(p, '{121} s{24}>>{344}g{34}>{34}<{344}f {--}')
		self.assertRenderEqual(p, '{121} s {24}>>{344}g{34}>{34}<{344}f {--}', width=10)
		# self.assertRenderEqual(p, '{121} s {24}>>{344}g{34}>{34}<{344} f {--}', width=11)
		self.assertEqual(list(p.render_above_lines()), [])

	def test_with_above(self):
		with replace_item(globals(), 'config', deepcopy(config)):
			old_segments = deepcopy(config['themes/test/default']['segments'])
			config['themes/test/default']['segments']['above'] = [old_segments]
			with get_powerline(run_once=True, simpler_renderer=True) as p:
				self.assertRenderLinesEqual(p, [
					'{121} s{24}>>{344}g{34}>{34}<{344}f {--}',
				])
				self.assertRenderLinesEqual(p, [
					'{121} s {24}>>{344}g{34}>{34}<{344}f {--}',
				], width=10)

			config['themes/test/default']['segments']['above'] = [old_segments] * 2
			with get_powerline(run_once=True, simpler_renderer=True) as p:
				self.assertRenderLinesEqual(p, [
					'{121} s{24}>>{344}g{34}>{34}<{344}f {--}',
					'{121} s{24}>>{344}g{34}>{34}<{344}f {--}',
				])
				self.assertRenderLinesEqual(p, [
					'{121} s {24}>>{344}g{34}>{34}<{344}f {--}',
					'{121} s {24}>>{344}g{34}>{34}<{344}f {--}',
				], width=10)


class TestColorschemesHierarchy(TestRender):
	@add_p_arg
	def test_group_redirects(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
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

	@add_p_arg
	def test_group_redirects_no_main(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
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

	@add_p_arg
	def test_group_redirects_no_top_default(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
			del config['colorschemes/default']
			config['themes/test/default']['segments'] = {
				'left': [
					highlighted_string('c', 'd3', draw_soft_divider=False),
					highlighted_string('C', 'm3', draw_hard_divider=False),
				],
				'right': [],
			}
			self.assertRenderEqual(p, '{1112} c{1112}C{--}')

	@add_p_arg
	def test_group_redirects_no_test_default(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
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

	@add_p_arg
	def test_group_redirects_only_main(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
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

	@add_p_arg
	def test_group_redirects_only_top_default(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
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

	@add_p_arg
	def test_group_redirects_only_test_default(self, p):
		with replace_item(globals(), 'config', deepcopy(config)):
			del config['colorschemes/default']
			del config['colorschemes/test/__main__']
			config['themes/test/default']['segments'] = {
				'left': [
					highlighted_string('s', 'str1', draw_hard_divider=False),
				],
				'right': [],
			}
			self.assertRenderEqual(p, '{121} s{--}')


class TestVim(TestCase):
	def test_environ_update(self):
		# Regression test: test that segment obtains environment from vim, not 
		# from os.environ.
		from powerline.vim import VimPowerline
		with vim_module._with('environ', TEST='abc'):
			with get_powerline_raw(VimPowerline) as powerline:
				window = vim_module.current.window
				window_id = 1
				winnr = window.number
				self.assertEqual(powerline.render(window, window_id, winnr), '%#Pl_3_8404992_4_192_underline#\xa0abc%#Pl_4_192_NONE_None_NONE#>>')
				vim_module._environ['TEST'] = 'def'
				self.assertEqual(powerline.render(window, window_id, winnr), '%#Pl_3_8404992_4_192_underline#\xa0def%#Pl_4_192_NONE_None_NONE#>>')


replaces = {}


def setUpModule():
	global replaces
	replaces = swap_attributes(globals(), powerline_module, replaces)
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'path')))


def tearDownModule():
	global replaces
	replaces = swap_attributes(globals(), powerline_module, replaces)
	sys.path.pop(0)


if __name__ == '__main__':
	from tests import main
	main()
