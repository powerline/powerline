#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import argparse
import os
import re

from time import sleep
from subprocess import check_call
from io import BytesIO

import pexpect


def get_argparser(ArgumentParser=argparse.ArgumentParser):
	parser = ArgumentParser(description='Run powerline shell test using pexpect')
	parser.add_argument('--wait-for-echo', action='store_true', help='Wait until the input is echoed back.')
	parser.add_argument('--type', metavar='TYPE', help='Test type (daemon, nodaemon, …).')
	parser.add_argument('--client', metavar='CLIENT', help='Type of the client used (C, shell, zpython, …).')
	parser.add_argument('--shell', metavar='SHELL', help='Shell name.')
	parser.add_argument('command', nargs=argparse.REMAINDER, metavar='COMMAND',
	                    help='Command to run and its argument.')
	return parser


def main():
	test_root = os.environ['TEST_ROOT']
	parser = get_argparser()
	args = parser.parse_args()

	shell = args.shell or args.command[0]
	test_type = args.type or shell
	test_client = args.client or test_type

	log_file_base = '{0}.{1}.{2}'.format(shell, test_type, test_client)
	full_log_file_name = os.path.join(test_root, '{0}.full.log'.format(log_file_base))

	local_paths = [
		os.path.abspath(os.path.join(test_root, 'path')),
		os.path.abspath('scripts'),
	]

	if test_type == 'fish':
		local_paths += ['/usr/bin', '/bin']

	python_paths = os.environ.get('PYTHONPATH', '')
	if python_paths:
		python_paths = ':' + python_paths
	python_paths = os.path.abspath('.') + python_paths

	environ = {
		'LANG': 'en_US.UTF-8',
		'PATH': os.pathsep.join(local_paths),
		'TERM': 'screen-256color',
		'DIR1': os.environ['DIR1'],
		'DIR2': os.environ['DIR2'],
		'XDG_CONFIG_HOME': os.path.abspath(os.path.join(test_root, 'fish_home')),
		'IPYTHONDIR': os.path.abspath(os.path.join(test_root, 'ipython_home')),
		'PYTHONPATH': python_paths,
		'POWERLINE_CONFIG_OVERRIDES': os.environ.get('POWERLINE_CONFIG_OVERRIDES', ''),
		'POWERLINE_THEME_OVERRIDES': os.environ.get('POWERLINE_THEME_OVERRIDES', ''),
		'POWERLINE_CONFIG_PATHS': os.path.abspath(os.path.join('powerline', 'config_files')),
		'POWERLINE_COMMAND_ARGS': os.environ.get('POWERLINE_COMMAND_ARGS', ''),
		'POWERLINE_COMMAND': os.environ.get('POWERLINE_COMMAND', ''),
		'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
		'TEST_ROOT': test_root,
	}

	os.environ['PATH'] = environ['PATH']

	if test_type == 'daemon':
		environ['POWERLINE_SHELL_CONTINUATION'] = '1'
		environ['POWERLINE_SHELL_SELECT'] = '1'

	if test_type != 'zpython' and shell == 'zsh':
		environ['POWERLINE_NO_ZSH_ZPYTHON'] = '1'

	sio = BytesIO()

	child = pexpect.spawn(
		args.command[0],
		args.command[1:],
		env=environ,
		logfile=sio,
		timeout=30,
	)
	child.expect(re.compile(b'.*'))
	sleep(0.5)
	child.setwinsize(1, 300)

	with open(os.path.join('tests', 'test_shells', 'inputs', shell), 'rb') as F:
		if not args.wait_for_echo:
			child.send(F.read())
		else:
			for line in F:
				child.send(line)
				sleep(1)
				# TODO Implement something more smart

	with open(full_log_file_name, 'wb') as LF:
		while True:
			try:
				s = child.read_nonblocking(1000)
			except pexpect.TIMEOUT:
				break
			except pexpect.EOF:
				break
			else:
				LF.write(s)

	child.close(force=True)

	check_call([
		os.path.join(test_root, 'path', 'python'),
		os.path.join('tests', 'test_shells', 'postproc.py'),
		test_type, test_client, shell
	])
	pidfile = os.path.join(test_root, '3rd', 'pid')
	if os.path.exists(pidfile):
		os.unlink(pidfile)


if __name__ == '__main__':
	main()
