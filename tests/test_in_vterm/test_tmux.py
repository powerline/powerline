#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import json

from time import sleep
from subprocess import check_call
from glob import glob1
from traceback import print_exc

from powerline.lib.dict import updated
from powerline.bindings.tmux import get_tmux_version
from powerline import get_fallback_logger

from tests.modules.lib.terminal import (ExpectProcess, MutableDimensions,
                                        do_terminal_tests, get_env)
from tests.modules import PowerlineTestSuite


TEST_ROOT = os.path.abspath(os.environ['TEST_ROOT'])


def tmux_logs_iter(test_dir):
	for tail in glob1(test_dir, '*.log'):
		yield os.path.join(test_dir, tail)


def print_tmux_logs():
	for f in tmux_logs_iter(TEST_ROOT):
		print('_' * 80)
		print(os.path.basename(f) + ':')
		print('=' * 80)
		with open(f, 'r') as fp:
			for line in fp:
				sys.stdout.write(line)
		os.unlink(f)


def get_expected_result(tmux_version,
                        expected_result_old,
                        expected_result_1_7=None,
                        expected_result_1_8=None,
                        expected_result_2_0=None):
	if tmux_version >= (2, 0) and expected_result_2_0:
		return expected_result_2_0
	elif tmux_version >= (1, 8) and expected_result_1_8:
		return expected_result_1_8
	elif tmux_version >= (1, 7) and expected_result_1_7:
		return expected_result_1_7
	else:
		return expected_result_old


def tmux_fin_cb(p, cmd, env):
	try:
		check_call([
			cmd, '-S', env['POWERLINE_TMUX_SOCKET_PATH'], 'kill-server'
		], env=env, cwd=TEST_ROOT)
	except Exception:
		print_exc()
	for f in tmux_logs_iter(TEST_ROOT):
		os.unlink(f)


def main(attempts=3):
	vterm_path = os.path.join(TEST_ROOT, 'path')

	tmux_exe = os.path.join(vterm_path, 'tmux')

	socket_path = os.path.abspath('tmux-socket-{0}'.format(attempts))
	if os.path.exists(socket_path):
		os.unlink(socket_path)

	env = get_env(vterm_path, TEST_ROOT, {
		'POWERLINE_THEME_OVERRIDES': ';'.join((
			key + '=' + json.dumps(val)
			for key, val in (
				('default.segments.right', [{
					'type': 'string',
					'name': 's1',
					'highlight_groups': ['cwd'],
					'priority':50,
				}]),
				('default.segments.left', [{
					'type': 'string',
					'name': 's2',
					'highlight_groups': ['background'],
					'priority':20,
				}]),
				('default.segment_data.s1.contents', 'S1 string here'),
				('default.segment_data.s2.contents', 'S2 string here'),
			)
		)),
		'POWERLINE_TMUX_SOCKET_PATH': socket_path,
	})

	conf_path = os.path.abspath('powerline/bindings/tmux/powerline.conf')
	conf_line = 'source "' + (
		conf_path.replace('\\', '\\\\').replace('"', '\\"')) + '"\n'
	conf_file = os.path.realpath(os.path.join(TEST_ROOT, 'tmux.conf'))
	with open(conf_file, 'w') as cf_fd:
		cf_fd.write(conf_line)

	tmux_version = get_tmux_version(get_fallback_logger())

	dim = MutableDimensions(rows=50, cols=200)

	def prepare_test_1(p):
		sleep(5)

	def prepare_test_2(p):
		dim.cols = 40
		p.resize(dim)
		sleep(5)

	base_attrs = {
		((0, 0, 0), (243, 243, 243), 1, 0, 0): 'lead',
		((243, 243, 243), (11, 11, 11), 0, 0, 0): 'leadsep',
		((255, 255, 255), (11, 11, 11), 0, 0, 0): 'bg',
		((199, 199, 199), (88, 88, 88), 0, 0, 0): 'cwd',
		((88, 88, 88), (11, 11, 11), 0, 0, 0): 'cwdhsep',
		((0, 0, 0), (0, 224, 0), 0, 0, 0): 'defstl',
	}
	tests = (
		{
			'expected_result': get_expected_result(
				tmux_version,
				expected_result_old=(
					'{lead: 0 }{leadsep: }{bg: S2 string here  }'
					'{4: 0  }{cwdhsep:| }{6:bash  }'
					'{bg: }{4: 1- }{cwdhsep:| }{6:bash  }'
					'{bg: }{7: }{8:2* | }{9:bash }{10: }'
					'{bg:' + (' ' * 124) + '}'
					'{cwdhsep: }{cwd: S1 string here }', updated(base_attrs, {
						((133, 133, 133), (11, 11, 11), 0, 0, 0): 4,
						((188, 188, 188), (11, 11, 11), 0, 0, 0): 6,
						((11, 11, 11), (0, 102, 153), 0, 0, 0): 7,
						((102, 204, 255), (0, 102, 153), 0, 0, 0): 8,
						((255, 255, 255), (0, 102, 153), 1, 0, 0): 9,
						((0, 102, 153), (11, 11, 11), 0, 0, 0): 10,
					})),
				expected_result_1_8=(
					'{lead: 0 }{leadsep: }{bg: S2 string here  }'
					'{4: 0  }{cwdhsep:| }{6:bash  }'
					'{bg: }{4: 1- }{cwdhsep:| }{7:bash  }'
					'{bg: }{8: }{9:2* | }{10:bash }{7: }'
					'{bg:' + (' ' * 124) + '}'
					'{cwdhsep: }{cwd: S1 string here }', updated(base_attrs, {
						((133, 133, 133), (11, 11, 11), 0, 0, 0): 4,
						((188, 188, 188), (11, 11, 11), 0, 0, 0): 6,
						((0, 102, 153), (11, 11, 11), 0, 0, 0): 7,
						((11, 11, 11), (0, 102, 153), 0, 0, 0): 8,
						((102, 204, 255), (0, 102, 153), 0, 0, 0): 9,
						((255, 255, 255), (0, 102, 153), 1, 0, 0): 10,
					})),
				expected_result_2_0=(
					'{lead: 0 }{leadsep: }{bg: S2 string here }'
					'{4: 0  }{cwdhsep:| }{6:bash  }'
					'{bg: }{4: 1- }{cwdhsep:| }{7:bash  }'
					'{bg: }{8: }{9:2* | }{10:bash }{7: }'
					'{bg:' + (' ' * 125) + '}'
					'{cwdhsep: }{cwd: S1 string here }', updated(base_attrs, {
						((133, 133, 133), (11, 11, 11), 0, 0, 0): 4,
						((188, 188, 188), (11, 11, 11), 0, 0, 0): 6,
						((0, 102, 153), (11, 11, 11), 0, 0, 0): 7,
						((11, 11, 11), (0, 102, 153), 0, 0, 0): 8,
						((102, 204, 255), (0, 102, 153), 0, 0, 0): 9,
						((255, 255, 255), (0, 102, 153), 1, 0, 0): 10,
					})),
			),
			'prep_cb': prepare_test_1,
			'row': dim.rows - 1,
		}, {
			'expected_result': get_expected_result(
				tmux_version,
				expected_result_old=('{bg:' + (' ' * 40) + '}', base_attrs),
				expected_result_1_7=(
					'{lead: 0 }'
					'{leadsep: }{bg: <}{4:h  }{bg: }{5: }'
					'{6:2* | }{7:bash }{8: }{bg: }{cwdhsep: }'
					'{cwd: S1 string here }', updated(base_attrs, {
						((188, 188, 188), (11, 11, 11), 0, 0, 0): 4,
						((11, 11, 11), (0, 102, 153), 0, 0, 0): 5,
						((102, 204, 255), (0, 102, 153), 0, 0, 0): 6,
						((255, 255, 255), (0, 102, 153), 1, 0, 0): 7,
						((0, 102, 153), (11, 11, 11), 0, 0, 0): 8,
					})),
				expected_result_1_8=(
					'{lead: 0 }'
					'{leadsep: }{bg: <}{4:h  }{bg: }{5: }'
					'{6:2* | }{7:bash }{4: }{bg: }{cwdhsep: }'
					'{cwd: S1 string here }', updated(base_attrs, {
						((0, 102, 153), (11, 11, 11), 0, 0, 0): 4,
						((11, 11, 11), (0, 102, 153), 0, 0, 0): 5,
						((102, 204, 255), (0, 102, 153), 0, 0, 0): 6,
						((255, 255, 255), (0, 102, 153), 1, 0, 0): 7,
					})),
				expected_result_2_0=(
					'{lead: 0 }'
					'{leadsep: }{bg:<}{4:ash  }{bg: }{5: }'
					'{6:2* | }{7:bash }{4: }{cwdhsep: }'
					'{cwd: S1 string here }', updated(base_attrs, {
						((0, 102, 153), (11, 11, 11), 0, 0, 0): 4,
						((11, 11, 11), (0, 102, 153), 0, 0, 0): 5,
						((102, 204, 255), (0, 102, 153), 0, 0, 0): 6,
						((255, 255, 255), (0, 102, 153), 1, 0, 0): 7,
					})),
			),
			'prep_cb': prepare_test_2,
			'row': dim.rows - 1,
		}
	)

	args = [
		# Specify full path to tmux socket (testing tmux instance must not 
		# interfere with user one)
		'-S', socket_path,
		# Force 256-color mode
		'-2',
		# Request verbose logging just in case
		'-v',
		# Specify configuration file
		'-f', conf_file,
		# Run bash three times
		'new-session', 'bash --norc --noprofile -i', ';',
		'new-window', 'bash --norc --noprofile -i', ';',
		'new-window', 'bash --norc --noprofile -i', ';',
	]

	with PowerlineTestSuite('tmux') as suite:
		return do_terminal_tests(
			tests=tests,
			cmd=tmux_exe,
			dim=dim,
			args=args,
			env=env,
			cwd=TEST_ROOT,
			fin_cb=tmux_fin_cb,
			last_attempt_cb=print_tmux_logs,
			suite=suite,
		)


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
