#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import json

from time import sleep
from subprocess import check_call
from difflib import ndiff
from glob import glob1

from powerline.lib.unicode import u
from powerline.lib.dict import updated
from powerline.bindings.tmux import get_tmux_version
from powerline import get_fallback_logger

from tests.lib.terminal import ExpectProcess


VTERM_TEST_DIR = os.path.abspath('tests/vterm_tmux')


def convert_expected_result(p, expected_result):
	return p.get_highlighted_text(expected_result, {})


def cell_properties_key_to_shell_escape(cell_properties_key):
	fg, bg, bold, underline, italic = cell_properties_key
	return('\x1b[38;2;{0};48;2;{1}{bold}{underline}{italic}m'.format(
		';'.join((str(i) for i in fg)),
		';'.join((str(i) for i in bg)),
		bold=(';1' if bold else ''),
		underline=(';4' if underline else ''),
		italic=(';3' if italic else ''),
	))


def test_expected_result(p, expected_result, cols, rows, print_logs):
	expected_text, attrs = expected_result
	attempts = 3
	result = None
	while attempts:
		actual_text, all_attrs = p.get_row(rows - 1, attrs)
		if actual_text == expected_text:
			return True
		attempts -= 1
		print('Actual result does not match expected. Attempts left: {0}.'.format(attempts))
		sleep(2)
	print('Result:')
	print(actual_text)
	print('Expected:')
	print(expected_text)
	print('Attributes:')
	print(all_attrs)
	p.send(b'powerline-config tmux setup\n')
	sleep(5)
	print('Screen:')
	screen, screen_attrs = p.get_screen(attrs)
	print(screen)
	print(screen_attrs)
	print('_' * 80)
	print('Diff:')
	print('=' * 80)
	print(''.join((u(line) for line in ndiff([actual_text], [expected_text]))))
	if print_logs:
		for f in glob1(VTERM_TEST_DIR, '*.log'):
			print('_' * 80)
			print(os.path.basename(f) + ':')
			print('=' * 80)
			with open(f, 'r') as F:
				for line in F:
					sys.stdout.write(line)
			os.unlink(f)
	return False


def get_expected_result(tmux_version,
                        expected_result_old,
                        expected_result_1_7=None,
                        expected_result_new=None,
                        expected_result_2_0=None):
	if tmux_version >= (2, 0) and expected_result_2_0:
		return expected_result_2_0
	elif tmux_version >= (1, 8) and expected_result_new:
		return expected_result_new
	elif tmux_version >= (1, 7) and expected_result_1_7:
		return expected_result_1_7
	else:
		return expected_result_old


def main(attempts=3):
	vterm_path = os.path.join(VTERM_TEST_DIR, 'path')
	socket_path = os.path.abspath('tmux-socket-{0}'.format(attempts))
	if os.path.exists(socket_path):
		os.unlink(socket_path)
	rows = 50
	cols = 200

	tmux_exe = os.path.join(vterm_path, 'tmux')

	if os.path.exists('tests/bot-ci/deps/libvterm/libvterm.so'):
		lib = 'tests/bot-ci/deps/libvterm/libvterm.so'
	else:
		lib = os.environ.get('POWERLINE_LIBVTERM', 'libvterm.so')

	env = {
		# Reasoning:
		# 1. vt* TERMs (used to be vt100 here) make tmux-1.9 use
		#    different and identical colors for inactive windows. This 
		#    is not like tmux-1.6: foreground color is different from 
		#    separator color and equal to (0, 102, 153) for some reason 
		#    (separator has correct color). tmux-1.8 is fine, so are 
		#    older versions (though tmux-1.6 and tmux-1.7 do not have 
		#    highlighting for previously active window) and my system 
		#    tmux-1.9a.
		# 2. screen, xterm and some other non-256color terminals both
		#    have the same issue and make libvterm emit complains like 
		#    `Unhandled CSI SGR 3231`.
		# 3. screen-256color, xterm-256color and other -256color
		#    terminals make libvterm emit complains about unhandled 
		#    escapes to stderr.
		# 4. `st-256color` does not have any of the above problems, but
		#    it may be not present on the target system because it is 
		#    installed with x11-terms/st and not with sys-libs/ncurses.
		#
		# For the given reasons decision was made: to fix tmux-1.9 tests 
		# and not make libvterm emit any data to stderr st-256color 
		# $TERM should be used, up until libvterm has its own terminfo 
		# database entry (if it ever will). To make sure that relevant 
		# terminfo entry is present on the target system it should be 
		# distributed with powerline test package. To make distribution 
		# not require modifying anything outside of powerline test 
		# directory TERMINFO variable is set.
		'TERMINFO': os.path.join(VTERM_TEST_DIR, 'terminfo'),
		'TERM': 'st-256color',
		'PATH': vterm_path,
		'SHELL': os.path.join(VTERM_TEST_DIR, 'path', 'bash'),
		'POWERLINE_CONFIG_PATHS': os.path.abspath('powerline/config_files'),
		'POWERLINE_COMMAND': 'powerline-render',
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
		'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
		'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
	}

	conf_path = os.path.abspath('powerline/bindings/tmux/powerline.conf')
	conf_line = 'source "' + (
		conf_path.replace('\\', '\\\\').replace('"', '\\"')) + '"\n'
	conf_file = os.path.realpath(os.path.join(VTERM_TEST_DIR, 'tmux.conf'))
	with open(conf_file, 'w') as cf_fd:
		cf_fd.write(conf_line)

	base_attrs = {
		((0, 0, 0), (243, 243, 243), 1, 0, 0): 'lead',
		((243, 243, 243), (11, 11, 11), 0, 0, 0): 'leadsep',
		((255, 255, 255), (11, 11, 11), 0, 0, 0): 'bg',
		((199, 199, 199), (88, 88, 88), 0, 0, 0): 'cwd',
		((88, 88, 88), (11, 11, 11), 0, 0, 0): 'cwdhsep',
		((0, 0, 0), (0, 224, 0), 0, 0, 0): 'defstl',
	}

	try:
		p = ExpectProcess(
			lib=lib,
			rows=rows,
			cols=cols,
			cmd=tmux_exe,
			args=[
				# Specify full path to tmux socket (testing tmux instance must 
				# not interfere with user one)
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
			],
			cwd=VTERM_TEST_DIR,
			env=env,
		)
		p.start()
		sleep(5)
		tmux_version = get_tmux_version(get_fallback_logger())
		expected_result = get_expected_result(
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
			expected_result_new=(
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
		)
		ret = None
		if not test_expected_result(p, expected_result, cols, rows, not attempts):
			if attempts:
				pass
				# Will rerun main later.
			else:
				ret = False
		elif ret is not False:
			ret = True
		cols = 40
		p.resize(rows, cols)
		sleep(5)
		expected_result = get_expected_result(
			tmux_version,
			expected_result_old=('{bg:' + (' ' * cols) + '}', base_attrs),
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
			expected_result_new=(
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
		)
		if not test_expected_result(p, expected_result, cols, rows, not attempts):
			if attempts:
				pass
			else:
				ret = False
		elif ret is not False:
			ret = True
		if ret is not None:
			return ret
	finally:
		p.kill()
		p.join(10)
		assert(not p.isAlive())
	return main(attempts=(attempts - 1))


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
