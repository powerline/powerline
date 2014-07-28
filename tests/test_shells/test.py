#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import absolute_import, unicode_literals, division, print_function

import os
import socket
import sys
import difflib
import codecs
import re

import pexpect
import pexpect.ANSI

from time import sleep
from io import StringIO
from shutil import rmtree
from subprocess import check_call

from powerline.lib.unicode import u, unicode
from powerline.renderer import NBSP, Renderer


SHELL_TESTS_ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS_ROOT = os.path.dirname(SHELL_TESTS_ROOT)
SHELL_ROOT = os.path.join(TESTS_ROOT, 'shell')
POWERLINE_ROOT = os.path.dirname(TESTS_ROOT)
THIRD_LEVEL_DIR = os.path.join(SHELL_ROOT, '3rd')


def cat_v_relaxed(output):
	translations = Renderer.np_character_translations.copy()
	translations.pop(ord('\n'))
	translations.pop(0x1B)
	for line in output:
		sys.stdout.write(line.translate(translations))


def cat_v(output):
	translations = Renderer.np_character_translations.copy()
	translations.pop(ord('\n'))
	return [
		line.translate(translations)
		for line in output
	]


NO_COLOR_RE = re.compile('\033\\[.*?m')


def nocolor(output):
	return [
		NO_COLOR_RE.subn('', line)[0]
		for line in output
	]


def ss(lines):
	return (line.encode('utf-8') if isinstance(line, unicode) else line
			for line in lines)


def check_output(shell, output, full_output):
	ok_file = os.path.join(SHELL_TESTS_ROOT, shell + '.ok')
	out_file = os.path.join(SHELL_ROOT, shell + '.out')
	with codecs.open(out_file, 'w', encoding='utf-8') as OF:
		OF.writelines(output)
	# The following does not work:
	# - Checking differences using output == expected_output without writing to
	#   file and reading back: lines do not differ, but they are split in 
	#   a different fashion.
	# - Checking differences using output == expected_output *after* writing to
	#   file and reading back with below code, even though I was not able to 
	#   find any differences between lists obtained that way.
	# - Checking differences using difflib.unified_diff() without writing to
	#   file and reading back: lines do not differ, but lists do.
	with codecs.open(out_file, encoding='utf-8') as OF:
		output = list(OF)
	if os.path.isfile(ok_file):
		with codecs.open(ok_file, encoding='utf-8') as OF:
			expected_output = list(OF)
		diff = list(difflib.unified_diff(output, expected_output))
		differs = bool(diff)
		if differs:
			sys.stdout.writelines(ss(diff))
			sys.stdout.writelines(ss(difflib.ndiff(
				cat_v(nocolor(output)),
				cat_v(nocolor(expected_output)),
			)))
			sys.stdout.writelines(ss(difflib.unified_diff(
				[repr(line) + '\n' for line in output],
				[repr(line) + '\n' for line in expected_output],
			)))
	else:
		differs = True
	if differs:
		maxlen = 80
		curlen = maxlen - len(' Output: ')
		print(('*' * (curlen // 2)) + ' Output: ' + ('*' * (curlen // 2)))
		cat_v_relaxed(output)
		curlen = maxlen - len(' Full output: ')
		print(('*' * (curlen // 2)) + ' Full output: ' + ('*' * (curlen // 2)))
		cat_v_relaxed(full_output)
		print('*' * maxlen)
	return differs


def run_test(debug, shell, args):
	# Other sizes do not work in any case (this neither does though: see 
	# pexpect/pexpect#97).
	lines = 24
	columns = 80
	env = {
		'LANG': 'en_US.UTF-8',
		'PATH': os.environ['PATH'],
		'USER': 'user',
		'DIR1': '\033[32m',
		'DIR2': '\b',
		'XDG_CONFIG_HOME': os.path.join(SHELL_ROOT, 'fish_home'),
		# Bash requires $TERM to be set to work properly
		'TERM': 'xterm',
	}

	try:
		child = pexpect.spawnu(shell, args, encoding='utf-8', env=env, cwd=POWERLINE_ROOT)
	# There is no more specific exception for not found command
	except pexpect.ExceptionPexpect:
		# Skip test when shell failed to launch
		return False

	child.setwinsize(lines, columns)

	started_test = False
	output = StringIO()
	full_output = StringIO()

	with open(os.path.join(SHELL_TESTS_ROOT, 'input.' + shell)) as IF:
		for line in IF:
			if not started_test and 'cd tests/shell/3rd' in line:
				started_test = True
			elif started_test and 'true is the last line' in line:
				started_test = False
			child.send(line)
			if started_test:
				current_output = ''
				while NBSP not in current_output:
					try:
						new_output = u(child.read_nonblocking(size=1000, timeout=0))
						if debug:
							cat_v_relaxed(new_output)
						current_output += new_output
					except pexpect.TIMEOUT:
						pass
					except pexpect.EOF:
						break
				output.write(current_output)
				if debug:
					cat_v_relaxed(current_output)
				full_output.write(current_output)
			else:
				sleep(0.25)
				try:
					current_output = u(child.read_nonblocking(size=1000, timeout=0))
					if debug:
						cat_v_relaxed(current_output)
					full_output.write(current_output)
				except pexpect.TIMEOUT:
					pass
				except pexpect.EOF:
					break

	output.seek(0)
	full_output.seek(0)
	return check_output(
		shell,
		postproc(output, os.path.join(THIRD_LEVEL_DIR, 'pid')),
		list(full_output)
	)


def postproc(lines, pid_fname):
	hostname = socket.gethostname()
	user = os.environ['USER']
	with open(pid_fname, 'r') as PF:
		pid = PF.read().strip()
	return [
		line.replace(hostname, 'HOST').replace(user, 'USER').replace(pid, 'PID')
		for line in lines
	]


SHELLS = {
	'bash': ['--norc', '--noprofile', '-i'],
	'zsh': ['-f', '-i'],
	'fish': ['-i'],
	'tcsh': ['-f', '-i'],
	'busybox': ['ash', '-i'],
	'mksh': ['-i'],
	'dash': ['-i'],
}


def main(debug=False, checked_shells=None):
	if os.path.exists(SHELL_ROOT):
		rmtree(SHELL_ROOT)
	os.mkdir(SHELL_ROOT)
	os.mkdir(os.path.join(SHELL_ROOT, 'fish_home'))
	os.mkdir(THIRD_LEVEL_DIR)
	for dname in (
		'\033[32m',
		'\b',
		'\\[\\]',
		'%%',
		'#[bold]',
		'(echo)',
		'$(echo)',
		'`echo`',
	):
		os.mkdir(os.path.join(THIRD_LEVEL_DIR, dname))
	check_call(('git', 'init', THIRD_LEVEL_DIR))
	check_call(('git', 'checkout', '-b', 'BR'), cwd=THIRD_LEVEL_DIR)
	ret = 0
	try:
		for shell in checked_shells:
			print ('Checking ' + shell)
			if run_test(debug, shell, SHELLS[shell]):
				ret = 1
	finally:
		if not ret:
			rmtree(SHELL_ROOT)
	return ret


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(
		description='Run powerline functional tests in various shells',
	)
	parser.add_argument('-d', '--debug', action='store_true',
						help='Enable some debugging output')
	all_shells = list(SHELLS)
	# Using `*` as nargs produces “invalid choice: []”
	parser.add_argument('shells', metavar='shell', nargs=argparse.REMAINDER,
						choices=all_shells,
						help='Only test those shells (default: all available)')
	args = parser.parse_args()
	sys.exit(main(args.debug, args.shells or all_shells))
