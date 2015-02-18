#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from time import sleep
from subprocess import check_call
from itertools import groupby
from difflib import ndiff

from powerline.lib.unicode import u
from powerline.bindings.tmux import get_tmux_version
from powerline import get_fallback_logger

from tests.lib.terminal import ExpectProcess


def cell_properties_key_to_shell_escape(cell_properties_key):
	fg, bg, bold, underline, italic = cell_properties_key
	return('\x1b[38;2;{0};48;2;{1}{bold}{underline}{italic}m'.format(
		';'.join((str(i) for i in fg)),
		';'.join((str(i) for i in bg)),
		bold=(';1' if bold else ''),
		underline=(';4' if underline else ''),
		italic=(';3' if italic else ''),
	))


def test_expected_result(p, expected_result, cols, rows):
	last_line = []
	for col in range(cols):
		last_line.append(p[rows - 1, col])
	attempts = 10
	result = None
	while attempts:
		result = tuple((
			(key, ''.join((i.text for i in subline)))
			for key, subline in groupby(last_line, lambda i: i.cell_properties_key)
		))
		if result == expected_result:
			return True
		attempts -= 1
		print('Actual result does not match expected. Attempts left: {0}.'.format(attempts))
		sleep(2)
	print('Result:')
	shesc_result = ''.join((
		'{0}{1}\x1b[m'.format(cell_properties_key_to_shell_escape(key), text)
		for key, text in result
	))
	print(shesc_result)
	print('Expected:')
	shesc_expected_result = ''.join((
		'{0}{1}\x1b[m'.format(cell_properties_key_to_shell_escape(key), text)
		for key, text in expected_result
	))
	print(shesc_expected_result)
	p.send(b'powerline-config tmux setup\n')
	sleep(5)
	print('Screen:')
	screen = []
	for i in range(rows):
		screen.append([])
		for j in range(cols):
			screen[-1].append(p[i, j])
	print('\n'.join(
		''.join((
			'{0}{1}\x1b[m'.format(
				cell_properties_key_to_shell_escape(i.cell_properties_key),
				i.text
			) for i in line
		))
		for line in screen
	))
	a = shesc_result.replace('\x1b', '\\e') + '\n'
	b = shesc_expected_result.replace('\x1b', '\\e') + '\n'
	print('_' * 80)
	print('Diff:')
	print('=' * 80)
	print(''.join((u(line) for line in ndiff([a], [b]))))
	return False


def main():
	VTERM_TEST_DIR = os.path.abspath('tests/vterm')
	vterm_path = os.path.join(VTERM_TEST_DIR, 'path')
	socket_path = os.path.join(VTERM_TEST_DIR, 'tmux-socket')
	rows = 50
	cols = 200

	tmux_exe = os.path.join(vterm_path, 'tmux')

	try:
		p = ExpectProcess(
			lib='tests/bot-ci/deps/libvterm/libvterm.so',
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
				'-f', os.path.abspath('powerline/bindings/tmux/powerline.conf'),
				# Run bash three times
				'new-session', 'bash --norc --noprofile -i', ';',
				'new-window', 'bash --norc --noprofile -i', ';',
				'new-window', 'bash --norc --noprofile -i', ';',
			],
			cwd=VTERM_TEST_DIR,
			env={
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
				'SHELL': os.path.join(''),
				'POWERLINE_CONFIG_PATHS': os.path.abspath('powerline/config_files'),
				'POWERLINE_COMMAND': 'powerline-render',
				'POWERLINE_THEME_OVERRIDES': (
					'default.segments.right=[{"type":"string","name":"s1","highlight_groups":["cwd"]}];'
					'default.segments.left=[{"type":"string","name":"s2","highlight_groups":["background"]}];'
					'default.segment_data.s1.contents=S1 string here;'
					'default.segment_data.s2.contents=S2 string here;'
				),
				'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
				'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
			},
		)
		p.start()
		sleep(2)
		expected_result_new = (
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' S2 string here  '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 0 '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 1 '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2 | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), '                                                                                                                               '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here '),
		)
		expected_result_old = (
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' S2 string here  '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 0 '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 1 '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2 | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), '                                                                                                                               '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here '),
		)
		tmux_version = get_tmux_version(get_fallback_logger())
		if tmux_version < (1, 8):
			expected_result = expected_result_old
		else:
			expected_result = expected_result_new
		return test_expected_result(p, expected_result, cols, rows)
	finally:
		check_call([tmux_exe, '-S', socket_path, 'kill-server'], env={
			'PATH': vterm_path,
			'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
		})


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
