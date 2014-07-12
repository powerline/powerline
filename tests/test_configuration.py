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
		},
		'gradients': {
		},
	},
	'colorschemes/test/default': {
		'groups': {
			'str1': {'fg': 'col1', 'bg': 'col2', 'attr': ['bold']},
			'str2': {'fg': 'col3', 'bg': 'col4', 'attr': ['underline']},
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
				{
					'type': 'string',
					'contents': 's',
					'width': 'auto',
					'highlight_group': ['str1'],
				},
				{
					'type': 'string',
					'contents': 'g',
					'highlight_group': ['str2'],
				},
			],
			'right': [
				{
					'type': 'string',
					'contents': 'f',
					'width': 'auto',
					'align': 'right',
					'highlight_group': ['str2'],
				},
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


class TestLines(TestCase):
	def assertRenderEqual(self, p, output, **kwargs):
		self.assertEqual(p.render(**kwargs).replace(' ', ' '), output)

	def assertRenderLinesEqual(self, p, output, **kwargs):
		self.assertEqual([l.replace(' ', ' ') for l in p.render_above_lines(**kwargs)], output)

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
