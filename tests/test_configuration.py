# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os

from functools import wraps
from copy import deepcopy

import tests.vim as vim_module

from tests import TestCase
from tests.lib.config_mock import get_powerline, get_powerline_raw, swap_attributes
from tests.lib import Args, replace_item


def highlighted_string(s, group, **kwargs):
	ret = {
		'type': 'string',
		'contents': s,
		'highlight_groups': [group],
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
			'shell': {
				'theme': 'default',
				'colorscheme': 'default',
			},
			'wm': {
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
			'm3': {'fg': 'col11', 'bg': 'col12', 'attrs': []},
		}
	},
	'colorschemes/default': {
		'groups': {
			'g1': {'fg': 'col5', 'bg': 'col6', 'attrs': []},
			'g2': {'fg': 'col7', 'bg': 'col8', 'attrs': []},
			'g3': {'fg': 'col9', 'bg': 'col10', 'attrs': []},
		}
	},
	'colorschemes/test/default': {
		'groups': {
			'str1': {'fg': 'col1', 'bg': 'col2', 'attrs': ['bold']},
			'str2': {'fg': 'col3', 'bg': 'col4', 'attrs': ['underline']},
			'd1': 'g2',
			'd2': 'm2',
			'd3': 'm3',
		},
	},
	'colorschemes/vim/default': {
		'groups': {
			'environment': {'fg': 'col3', 'bg': 'col4', 'attrs': ['underline']},
		},
	},
	'colorschemes/wm/default': {
		'groups': {
			'hl1': {'fg': 'col1', 'bg': 'col2', 'attrs': ['underline']},
			'hl2': {'fg': 'col2', 'bg': 'col1', 'attrs': []},
			'hl3': {'fg': 'col3', 'bg': 'col1', 'attrs': ['underline']},
			'hl4': {'fg': 'col2', 'bg': 'col4', 'attrs': []},
		},
	},
	'themes/test/default': {
		'segments': {
			'left': [
				highlighted_string('s', 'str1', width='auto'),
				highlighted_string('g', 'str2'),
			],
			'right': [
				highlighted_string('f', 'str2', width='auto', align='r'),
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
		'segments': {
			'left': [
				{
					'function': 'powerline.segments.common.env.environment',
					'args': {
						'variable': 'TEST',
					},
				},
			],
		},
	},
	'themes/shell/default': {
		'default_module': 'powerline.segments.common',
		'segments': {
			'left': [
				highlighted_string('s', 'g1', width='auto'),
			],
		},
	},
	'themes/wm/default': {
		'default_module': 'powerline.segments.common',
		'segments': {
			'left': [
				highlighted_string('A', 'hl1'),
				highlighted_string('B', 'hl2'),
			],
			'right': [
				highlighted_string('C', 'hl3'),
				highlighted_string('D', 'hl4'),
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


class TestDisplayCondition(TestRender):
	@add_args
	def test_include_modes(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s1', 'g1', include_modes=['m1']),
				highlighted_string('s2', 'g1', include_modes=['m1', 'm2']),
				highlighted_string('s3', 'g1', include_modes=['m3']),
			]
		}
		self.assertRenderEqual(p, '{--}')
		self.assertRenderEqual(p, '{56} s1{56}>{56}s2{6-}>>{--}', mode='m1')
		self.assertRenderEqual(p, '{56} s2{6-}>>{--}', mode='m2')
		self.assertRenderEqual(p, '{56} s3{6-}>>{--}', mode='m3')

	@add_args
	def test_exclude_modes(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s1', 'g1', exclude_modes=['m1']),
				highlighted_string('s2', 'g1', exclude_modes=['m1', 'm2']),
				highlighted_string('s3', 'g1', exclude_modes=['m3']),
			]
		}
		self.assertRenderEqual(p, '{56} s1{56}>{56}s2{56}>{56}s3{6-}>>{--}')
		self.assertRenderEqual(p, '{56} s3{6-}>>{--}', mode='m1')
		self.assertRenderEqual(p, '{56} s1{56}>{56}s3{6-}>>{--}', mode='m2')
		self.assertRenderEqual(p, '{56} s1{56}>{56}s2{6-}>>{--}', mode='m3')

	@add_args
	def test_exinclude_modes(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s1', 'g1', exclude_modes=['m1'], include_modes=['m2']),
				highlighted_string('s2', 'g1', exclude_modes=['m1', 'm2'], include_modes=['m3']),
				highlighted_string('s3', 'g1', exclude_modes=['m3'], include_modes=['m3']),
			]
		}
		self.assertRenderEqual(p, '{--}')
		self.assertRenderEqual(p, '{--}', mode='m1')
		self.assertRenderEqual(p, '{56} s1{6-}>>{--}', mode='m2')
		self.assertRenderEqual(p, '{56} s2{6-}>>{--}', mode='m3')

	@add_args
	def test_exinclude_function_nonexistent_module(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s1', 'g1', exclude_function='xxx_nonexistent_module.foo'),
				highlighted_string('s2', 'g1', exclude_function='xxx_nonexistent_module.foo', include_function='xxx_nonexistent_module.bar'),
				highlighted_string('s3', 'g1', include_function='xxx_nonexistent_module.bar'),
			]
		}
		self.assertRenderEqual(p, '{56} s1{56}>{56}s2{56}>{56}s3{6-}>>{--}')

	@add_args
	def test_exinclude_function(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s1', 'g1', exclude_function='mod.foo'),
				highlighted_string('s2', 'g1', exclude_function='mod.foo', include_function='mod.bar'),
				highlighted_string('s3', 'g1', include_function='mod.bar'),
			]
		}
		launched = set()
		fool = [None]
		barl = [None]

		def foo(*args, **kwargs):
			launched.add('foo')
			self.assertEqual(set(kwargs.keys()), set(('pl', 'segment_info', 'mode')))
			self.assertEqual(args, ())
			return fool[0]

		def bar(*args, **kwargs):
			launched.add('bar')
			self.assertEqual(set(kwargs.keys()), set(('pl', 'segment_info', 'mode')))
			self.assertEqual(args, ())
			return barl[0]

		with replace_item(sys.modules, 'mod', Args(foo=foo, bar=bar)):
			fool[0] = True
			barl[0] = True
			self.assertRenderEqual(p, '{56} s3{6-}>>{--}')
			self.assertEqual(launched, set(('foo', 'bar')))

			fool[0] = False
			barl[0] = True
			self.assertRenderEqual(p, '{56} s1{56}>{56}s2{56}>{56}s3{6-}>>{--}')
			self.assertEqual(launched, set(('foo', 'bar')))

			fool[0] = False
			barl[0] = False
			self.assertRenderEqual(p, '{56} s1{6-}>>{--}')
			self.assertEqual(launched, set(('foo', 'bar')))

			fool[0] = True
			barl[0] = False
			self.assertRenderEqual(p, '{--}')
			self.assertEqual(launched, set(('foo', 'bar')))

	@add_args
	def test_exinclude_modes_override_functions(self, p, config):
		config['themes/test/default']['segments'] = {
			'left': [
				highlighted_string('s1', 'g1', exclude_function='mod.foo', exclude_modes=['m2']),
				highlighted_string('s2', 'g1', exclude_function='mod.foo', include_modes=['m2']),
				highlighted_string('s3', 'g1', include_function='mod.foo', exclude_modes=['m2']),
				highlighted_string('s4', 'g1', include_function='mod.foo', include_modes=['m2']),
			]
		}
		fool = [None]

		def foo(*args, **kwargs):
			return fool[0]

		with replace_item(sys.modules, 'mod', Args(foo=foo)):
			fool[0] = True
			self.assertRenderEqual(p, '{56} s4{6-}>>{--}', mode='m2')
			self.assertRenderEqual(p, '{56} s3{56}>{56}s4{6-}>>{--}', mode='m1')

			fool[0] = False
			self.assertRenderEqual(p, '{56} s2{56}>{56}s4{6-}>>{--}', mode='m2')
			self.assertRenderEqual(p, '{56} s1{6-}>>{--}', mode='m1')


class TestSegmentAttributes(TestRender):
	@add_args
	def test_no_attributes(self, p, config):
		def m1(divider=',', **kwargs):
			return divider.join(kwargs.keys()) + divider
		config['themes/test/default']['segments'] = {
			'left': [
				{
					'function': 'bar.m1'
				}
			]
		}
		with replace_item(sys.modules, 'bar', Args(m1=m1)):
			self.assertRenderEqual(p, '{56} pl,{6-}>>{--}')

	@add_args
	def test_segment_datas(self, p, config):
		def m1(divider=',', **kwargs):
			return divider.join(kwargs.keys()) + divider
		m1.powerline_segment_datas = {
			'powerline': {
				'args': {
					'divider': ';'
				}
			},
			'ascii': {
				'args': {
					'divider': '--'
				}
			}
		}
		config['themes/test/default']['segments'] = {
			'left': [
				{
					'function': 'bar.m1'
				}
			]
		}
		with replace_item(sys.modules, 'bar', Args(m1=m1)):
			self.assertRenderEqual(p, '{56} pl;{6-}>>{--}')

	@add_args
	def test_expand(self, p, config):
		def m1(divider=',', **kwargs):
			return divider.join(kwargs.keys()) + divider

		def expand(pl, amount, segment, **kwargs):
			return ('-' * amount) + segment['contents']

		m1.expand = expand
		config['themes/test/default']['segments'] = {
			'left': [
				{
					'function': 'bar.m1',
					'width': 'auto'
				}
			]
		}
		with replace_item(sys.modules, 'bar', Args(m1=m1)):
			self.assertRenderEqual(p, '{56} ----pl,{6-}>>{--}', width=10)

	@add_args
	def test_truncate(self, p, config):
		def m1(divider=',', **kwargs):
			return divider.join(kwargs.keys()) + divider

		def truncate(pl, amount, segment, **kwargs):
			return segment['contents'][:-amount]

		m1.truncate = truncate
		config['themes/test/default']['segments'] = {
			'left': [
				{
					'function': 'bar.m1'
				}
			]
		}
		with replace_item(sys.modules, 'bar', Args(m1=m1)):
			self.assertRenderEqual(p, '{56} p{6-}>>{--}', width=4)


class TestSegmentData(TestRender):
	@add_args
	def test_segment_data(self, p, config):
		def m1(**kwargs):
			return 'S'

		def m2(**kwargs):
			return 'S'
		sys.modules['bar'] = Args(m1=m1, m2=m2)
		config['themes/powerline']['segment_data'] = {
			'm1': {
				'before': '1'
			},
			'bar.m2': {
				'before': '2'
			},
			'n': {
				'before': '3'
			},
			'm2': {
				'before': '4'
			},
		}
		config['themes/test/default']['segments'] = {
			'left': [
				{
					'function': 'bar.m1'
				},
				{
					'function': 'bar.m1',
					'name': 'n'
				},
				{
					'function': 'bar.m2',
					'name': 'n'
				},
				{
					'function': 'bar.m2'
				}
			]
		}
		self.assertRenderEqual(p, '{56} 1S{56}>{56}3S{610}>>{910}3S{910}>{910}2S{10-}>>{--}')


class TestShellEscapes(TestCase):
	@with_new_config
	def test_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1b[0;38;5;5;48;5;6m\xa0s\x1b[0;38;5;6;49;22m>>\x1b[0m')

	@with_new_config
	def test_tmux_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['additional_escapes'] = 'tmux'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1bPtmux;\x1b\x1b[0;38;5;5;48;5;6m\x1b\\\xa0s\x1bPtmux;\x1b\x1b[0;38;5;6;49;22m\x1b\\>>\x1bPtmux;\x1b\x1b[0m\x1b\\')

	@with_new_config
	def test_screen_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['additional_escapes'] = 'screen'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1bP\x1b\x1b[0;38;5;5;48;5;6m\x1b\\\xa0s\x1bP\x1b\x1b[0;38;5;6;49;22m\x1b\\>>\x1bP\x1b\x1b[0m\x1b\\')

	@with_new_config
	def test_fbterm_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_escape_style'] = 'fbterm'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1b[0m\x1b[1;5}\x1b[2;6}\xa0s\x1b[0m\x1b[1;6}\x1b[49m\x1b[22m>>\x1b[0m')

	@with_new_config
	def test_fbterm_tmux_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_escape_style'] = 'fbterm'
		config['config']['common']['additional_escapes'] = 'tmux'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1bPtmux;\x1b\x1b[0m\x1b\x1b[1;5}\x1b\x1b[2;6}\x1b\\\xa0s\x1bPtmux;\x1b\x1b[0m\x1b\x1b[1;6}\x1b\x1b[49m\x1b\x1b[22m\x1b\\>>\x1bPtmux;\x1b\x1b[0m\x1b\\')

	@with_new_config
	def test_fbterm_screen_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_escape_style'] = 'fbterm'
		config['config']['common']['additional_escapes'] = 'screen'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1bP\x1b\x1b[0m\x1b\x1b[1;5}\x1b\x1b[2;6}\x1b\\\xa0s\x1bP\x1b\x1b[0m\x1b\x1b[1;6}\x1b\x1b[49m\x1b\x1b[22m\x1b\\>>\x1bP\x1b\x1b[0m\x1b\\')

	@with_new_config
	def test_term_truecolor_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_truecolor'] = True
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1b[0;38;2;192;0;192;48;2;0;128;128m\xa0s\x1b[0;38;2;0;128;128;49;22m>>\x1b[0m')

	@with_new_config
	def test_term_truecolor_fbterm_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_escape_style'] = 'fbterm'
		config['config']['common']['term_truecolor'] = True
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1b[0m\x1b[1;5}\x1b[2;6}\xa0s\x1b[0m\x1b[1;6}\x1b[49m\x1b[22m>>\x1b[0m')

	@with_new_config
	def test_term_truecolor_tmux_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_truecolor'] = True
		config['config']['common']['additional_escapes'] = 'tmux'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1bPtmux;\x1b\x1b[0;38;2;192;0;192;48;2;0;128;128m\x1b\\\xa0s\x1bPtmux;\x1b\x1b[0;38;2;0;128;128;49;22m\x1b\\>>\x1bPtmux;\x1b\x1b[0m\x1b\\')

	@with_new_config
	def test_term_truecolor_screen_escapes(self, config):
		from powerline.shell import ShellPowerline
		import powerline as powerline_module
		config['config']['common']['term_truecolor'] = True
		config['config']['common']['additional_escapes'] = 'screen'
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, ShellPowerline, args=Args(config_path=[''])) as powerline:
				self.assertEqual(powerline.render(segment_info={}, side='left'), '\x1bP\x1b\x1b[0;38;2;192;0;192;48;2;0;128;128m\x1b\\\xa0s\x1bP\x1b\x1b[0;38;2;0;128;128;49;22m\x1b\\>>\x1bP\x1b\x1b[0m\x1b\\')


class TestVim(TestCase):
	def test_environ_update(self):
		# Regression test: test that segment obtains environment from vim, not 
		# from os.environ.
		import tests.vim as vim_module
		with vim_module._with('globals', powerline_config_paths=['/']):
			from powerline.vim import VimPowerline
			import powerline as powerline_module
			with swap_attributes(config, powerline_module):
				with vim_module._with('environ', TEST='abc'):
					with get_powerline_raw(config, VimPowerline) as powerline:
						window = vim_module.current.window
						window_id = 1
						winnr = window.number
						self.assertEqual(powerline.render(window, window_id, winnr), b'%#Pl_3_8404992_4_192_underline#\xc2\xa0abc%#Pl_4_192_NONE_None_NONE#>>')
						vim_module._environ['TEST'] = 'def'
						self.assertEqual(powerline.render(window, window_id, winnr), b'%#Pl_3_8404992_4_192_underline#\xc2\xa0def%#Pl_4_192_NONE_None_NONE#>>')

	def test_local_themes(self):
		# Regression test: VimPowerline.add_local_theme did not work properly.
		from powerline.vim import VimPowerline
		import powerline as powerline_module
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, VimPowerline, replace_gcp=True) as powerline:
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
								'highlight_groups': ['g1']
							}
						]
					}
				})
				window = vim_module.current.window
				window_id = 1
				winnr = window.number
				self.assertEqual(powerline.render(window, window_id, winnr), b'%#Pl_5_12583104_6_32896_NONE#\xc2\xa0\xe2\x80\x9cbar\xe2\x80\x9d%#Pl_6_32896_NONE_None_NONE#>>')

	@classmethod
	def setUpClass(cls):
		sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'path')))

	@classmethod
	def tearDownClass(cls):
		sys.path.pop(0)


class TestBar(TestRender):
	def test_bar(self):
		import powerline as powerline_module
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, powerline_module.Powerline, replace_gcp=True, ext='wm', renderer_module='bar') as powerline:
				self.assertRenderEqual(
					powerline,
					'%{l}%{F#ffc00000}%{B#ff008000}%{+u} A%{F-B--u}%{F#ff008000}%{B#ffc00000}>>%{F-B--u}%{F#ff008000}%{B#ffc00000}B%{F-B--u}%{F#ffc00000}>>%{F-B--u}%{r}%{F#ffc00000}<<%{F-B--u}%{F#ff804000}%{B#ffc00000}%{+u}C%{F-B--u}%{F#ff0000c0}%{B#ffc00000}<<%{F-B--u}%{F#ff008000}%{B#ff0000c0}D %{F-B--u}'
				)

	@with_new_config
	def test_bar_escape(self, config):
		import powerline as powerline_module
		config['themes/wm/default']['segments']['left'] = (
			highlighted_string('%{asd}', 'hl1'),
			highlighted_string('10% %', 'hl2'),
		)
		with swap_attributes(config, powerline_module):
			with get_powerline_raw(config, powerline_module.Powerline, replace_gcp=True, ext='wm', renderer_module='bar') as powerline:
				self.assertRenderEqual(
					powerline,
					'%{l}%{F#ffc00000}%{B#ff008000}%{+u} %%{asd}%{F-B--u}%{F#ff008000}%{B#ffc00000}>>%{F-B--u}%{F#ff008000}%{B#ffc00000}10%% %%%{F-B--u}%{F#ffc00000}>>%{F-B--u}%{r}%{F#ffc00000}<<%{F-B--u}%{F#ff804000}%{B#ffc00000}%{+u}C%{F-B--u}%{F#ff0000c0}%{B#ffc00000}<<%{F-B--u}%{F#ff008000}%{B#ff0000c0}D %{F-B--u}'
				)


if __name__ == '__main__':
	from tests import main
	main()
