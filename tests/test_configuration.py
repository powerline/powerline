# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import, division
import powerline as powerline_module
from tests import TestCase
from tests.lib import replace_item
from tests.lib.config_mock import swap_attributes, get_powerline, pop_events
from functools import wraps
from copy import deepcopy


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
}


def add_p_arg(func):
	@wraps(func)
	def f(self):
		with get_powerline(run_once=True, simpler_renderer=True) as p:
			func(self, p)
	return f


class TestSingleLine(TestCase):
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


replaces = {}


def setUpModule():
	global replaces
	replaces = swap_attributes(globals(), powerline_module, replaces)


tearDownModule = setUpModule


if __name__ == '__main__':
	from tests import main
	main()
