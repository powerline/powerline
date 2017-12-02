#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys

from time import sleep
from subprocess import check_call
from glob import glob1
from traceback import print_exc

from argparse import ArgumentParser

from powerline.lib.dict import updated

from tests.modules.lib.terminal import (ExpectProcess, MutableDimensions,
                                        do_terminal_tests, get_env)
from tests.modules import PowerlineTestSuite


TEST_ROOT = os.path.abspath(os.environ['TEST_ROOT'])


def get_parser():
	parser = ArgumentParser()
	parser.add_argument('--type', action='store')
	parser.add_argument('--client', action='store')
	parser.add_argument('--binding', action='store')
	parser.add_argument('args', action='append')
	return parser


BINDING_OPTIONS = {
	'dash': {
		'cmd': 'dash',
		'args': ['-i'],
		'init': [
			'. "$ROOT/tests/test_in_vterm/shell/inits/dash"',
		],
	},
}


def main(argv):
	script_args = get_parser().parse_args(argv)

	vterm_path = os.path.join(TEST_ROOT, 'path')

	env = get_env(vterm_path, TEST_ROOT)
	env['ROOT'] = os.path.abspath('.')
	env['TEST_ROOT'] = TEST_ROOT
	env['TEST_TYPE'] = script_args.type
	env['TEST_CLIENT'] = script_args.client
	env['LANG'] = 'en_US.UTF_8'
	env['_POWERLINE_RUNNING_SHELL_TESTS'] = (
		'ee5bcdc6-b749-11e7-9456-50465d597777')

	dim = MutableDimensions(rows=50, cols=200)

	binding_opts = BINDING_OPTIONS[script_args.binding]

	cmd = os.path.join(vterm_path, binding_opts['cmd'])
	args = binding_opts['args']

	def gen_init(binding):
		def init(p):
			for line in binding_opts['init']:
				p.send(line + '\n')
			sleep(1)

		return init

	def gen_feed(line):
		def feed(p):
			p.send(line + '\n')
			sleep(0.1)

		return feed

	base_attrs = {
		((255, 204,0), (204, 51, 0), 0, 0, 0): 'H',
		((204, 51, 0), (0, 102, 153), 0, 0, 0): 'sHU',
		((255, 255, 255), (0, 102, 153), 1, 0, 0): 'U',
		((0, 102, 153), (44, 44, 44), 0, 0, 0): 'sUB',
		((199, 199, 199), (44, 44, 44), 0, 0, 0): 'B',
		((44, 44, 44), (88, 88, 88), 0, 0, 0): 'sBD',
		((199, 199, 199), (88, 88, 88), 0, 0, 0): 'D',
		((144, 144, 144), (88, 88, 88), 0, 0, 0): 'sD',
		((221, 221, 221), (88, 88, 88), 1, 0, 0): 'C',
		((88, 88, 88), (0, 0, 0), 0, 0, 0): 'sDN',
		((240, 240, 240), (0, 0, 0), 0, 0, 0): 'N',
		((0, 102, 153), (51, 153, 204), 0, 0, 0): 'sUE',
		((255, 255, 255), (51, 153, 204), 0, 0, 0): 'E',
		((51, 153, 204), (44, 44, 44), 0, 0, 0): 'sEB',
	}

	tests = (
		{
			'expected_result': (
				'{H:  hostname }{sHU: }'
				'{U:user }{sUB: }'
				'{B: BRANCH }{sBD: }'
				'{D:… }{sD: }{D:tmp }{sD: }{D:vshells }{sD: }{C:3rd }{sDN: }'
				'{N:}',
				base_attrs,
			),
			'prep_cb': gen_init(script_args.binding),
		},
		{
			'expected_result': (
				'{H:  hostname }{sHU: }'
				'{U:user }{sUB: }'
				'{B: BRANCH }{sBD: }'
				'{D:… }{sD: }{D:vshells }{sD: }{D:3rd }{sD: }{C:.git }{sDN: }'
				'{N:}',
				base_attrs
			),
			'prep_cb': gen_feed('cd .git'),
		},
		{
			'expected_result': (
				'{H:  hostname }{sHU: }'
				'{U:user }{sUB: }'
				'{B: BRANCH }{sBD: }'
				'{D:… }{sD: }{D:tmp }{sD: }{D:vshells }{sD: }{C:3rd }{sDN: }'
				'{N:}',
				base_attrs,
			),
			'prep_cb': gen_feed('cd ..'),
		},
		{
			'expected_result': (
				'{H:  hostname }{sHU: }'
				'{U:user }{sUE: }'
				'{E:(e) some-venv }{sEB: }'
				'{B: BRANCH }{sBD: }'
				'{D:… }{sD: }{D:tmp }{sD: }{D:vshells }{sD: }{C:3rd }{sDN: }'
				'{N:}',
				base_attrs,
			),
			'prep_cb': gen_feed('set_virtual_env some-venv'),
		},
	)

	with PowerlineTestSuite('shell') as suite:
		return do_terminal_tests(
			tests=tests,
			cmd=cmd,
			dim=dim,
			args=args,
			env=env,
			cwd=TEST_ROOT,
			suite=suite,
		)


if __name__ == '__main__':
	if main(sys.argv[1:]):
		raise SystemExit(0)
	else:
		raise SystemExit(1)
