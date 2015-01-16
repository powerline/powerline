#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from time import sleep
from subprocess import check_call
from itertools import groupby
from difflib import ndiff

from powerline.lib.unicode import u

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
				'TERM': 'vt100',
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
			},
		)
		p.start()
		sleep(1)
		last_line = []
		for col in range(cols):
			last_line.append(p[rows - 1, col])
		result = tuple((
			(key, ''.join((i.text for i in subline)))
			for key, subline in groupby(last_line, lambda i: i.cell_properties_key)
		))
		expected_result = (
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
		if result == expected_result:
			return True
		else:
			a = shesc_result.replace('\x1b', '\\e') + '\n'
			b = shesc_expected_result.replace('\x1b', '\\e') + '\n'
			print('_' * 80)
			print('Diff:')
			print('=' * 80)
			print(''.join((u(line) for line in ndiff([a], [b]))))
			return False
	finally:
		check_call([tmux_exe, '-S', socket_path, 'kill-server'], env={
			'PATH': vterm_path,
		})


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
