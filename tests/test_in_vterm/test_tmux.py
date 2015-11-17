#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys

from time import sleep
from subprocess import check_call
from itertools import groupby
from difflib import ndiff
from glob import glob1

from powerline.lib.unicode import u
from powerline.bindings.tmux import get_tmux_version
from powerline import get_fallback_logger

from tests.lib.terminal import ExpectProcess


VTERM_TEST_DIR = os.path.abspath('tests/vterm_tmux')


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
	last_line = []
	for col in range(cols):
		last_line.append(p[rows - 1, col])
	attempts = 3
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
	print(result)
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


def get_expected_result(tmux_version, expected_result_old, expected_result_1_7=None, expected_result_new=None, expected_result_2_0=None):
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
	socket_path = 'tmux-socket'
	rows = 50
	cols = 200

	tmux_exe = os.path.join(vterm_path, 'tmux')

	if os.path.exists('tests/bot-ci/deps/libvterm/libvterm.so'):
		lib = 'tests/bot-ci/deps/libvterm/libvterm.so'
	else:
		lib = os.environ.get('POWERLINE_LIBVTERM', 'libvterm.so')

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
				'SHELL': os.path.join(VTERM_TEST_DIR, 'path', 'bash'),
				'POWERLINE_CONFIG_PATHS': os.path.abspath('powerline/config_files'),
				'POWERLINE_COMMAND': 'powerline-render',
				'POWERLINE_THEME_OVERRIDES': (
					'default.segments.right=[{"type":"string","name":"s1","highlight_groups":["cwd"],"priority":50}];'
					'default.segments.left=[{"type":"string","name":"s2","highlight_groups":["background"],"priority":20}];'
					'default.segment_data.s1.contents=S1 string here;'
					'default.segment_data.s2.contents=S2 string here;'
				),
				'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
				'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
			},
		)
		p.start()
		sleep(5)
		tmux_version = get_tmux_version(get_fallback_logger())
		expected_result = get_expected_result(tmux_version, expected_result_old=(
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' S2 string here  '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 0  '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 1- '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2* | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' ' * 124),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here '),
		), expected_result_new=(
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' S2 string here  '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 0  '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 1- '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2* | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' ' * 124),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here '),
		), expected_result_2_0=(
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' S2 string here '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 0  '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((133, 133, 133), (11, 11, 11), 0, 0, 0), ' 1- '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), '| '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), 'bash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2* | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' ' * 125),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here '),
		))
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
		expected_result = get_expected_result(tmux_version, (
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' ' * cols),
		), expected_result_1_7=(
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' <'),
			(((188, 188, 188), (11, 11, 11), 0, 0, 0), 'h  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2* | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here ')
		), expected_result_new=(
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' <'),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), 'h  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2* | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here ')
		), expected_result_2_0=(
			(((0, 0, 0), (243, 243, 243), 1, 0, 0), ' 0 '),
			(((243, 243, 243), (11, 11, 11), 0, 0, 0), ' '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), '<'),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), 'ash  '),
			(((255, 255, 255), (11, 11, 11), 0, 0, 0), ' '),
			(((11, 11, 11), (0, 102, 153), 0, 0, 0), ' '),
			(((102, 204, 255), (0, 102, 153), 0, 0, 0), '2* | '),
			(((255, 255, 255), (0, 102, 153), 1, 0, 0), 'bash '),
			(((0, 102, 153), (11, 11, 11), 0, 0, 0), ' '),
			(((88, 88, 88), (11, 11, 11), 0, 0, 0), ' '),
			(((199, 199, 199), (88, 88, 88), 0, 0, 0), ' S1 string here ')
		))
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
		check_call([tmux_exe, '-S', socket_path, 'kill-server'], env={
			'PATH': vterm_path,
			'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
		}, cwd=VTERM_TEST_DIR)
	return main(attempts=(attempts - 1))


if __name__ == '__main__':
	if main():
		raise SystemExit(0)
	else:
		raise SystemExit(1)
