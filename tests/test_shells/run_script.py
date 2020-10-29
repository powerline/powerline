#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import argparse
import os
import platform
import re
import socket

from time import sleep
from io import BytesIO

import pexpect


def run_main(shell, test_type, test_root, commands, wait_for_echo, client):

	local_paths = [
		os.path.abspath(os.path.join(test_root, 'path')),
		os.path.abspath('scripts'),
		os.path.abspath('client'),
		os.path.abspath(os.path.dirname(__file__))
	]

	if test_type == 'fish':
		local_paths += ['/usr/bin', '/bin']

	python_paths = os.environ.get('PYTHONPATH', '')
	if python_paths:
		python_paths = ':' + python_paths
	python_paths = os.path.abspath('.') + python_paths
	local_paths.append(os.environ["PATH"])

	environ = {
		'LANG': 'en_US.UTF-8',
		'PATH': os.pathsep.join(local_paths),
		'TERM': 'screen-256color',
		'DIR1': "[32m",
		'DIR2': "",
		'XDG_CONFIG_HOME': os.path.abspath(os.path.join(test_root, 'fish_home')),
		'IPYTHONDIR': os.path.abspath(os.path.join(test_root, 'ipython_home')),
		'PYTHONPATH': python_paths,
		'POWERLINE_CONFIG_OVERRIDES': os.environ.get('POWERLINE_CONFIG_OVERRIDES', ''),
		'POWERLINE_THEME_OVERRIDES': os.environ.get('POWERLINE_THEME_OVERRIDES', ''),
		'POWERLINE_CONFIG_PATHS': os.path.abspath(os.path.join('powerline', 'config_files')),
		'POWERLINE_COMMAND_ARGS': os.environ.get('POWERLINE_COMMAND_ARGS', ''),
		'POWERLINE_COMMAND': client,
		'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
		'TEST_ROOT': test_root,
	}

	if test_type == 'daemon':
		environ["POWERLINE_COMMAND_ARGS"] = "--socket /tmp/powerline-ipc-test-{}".format(os.getpid())
		environ['POWERLINE_SHELL_CONTINUATION'] = '1'
		environ['POWERLINE_SHELL_SELECT'] = '1'

	sio = BytesIO()

	child = pexpect.spawn(
		commands[0],
		commands[1:],
		env=environ,
		logfile=sio,
		timeout=30,
	)
	child.expect(re.compile(b'.*'))
	sleep(0.5)
	child.setwinsize(1, 300)

	with open(os.path.join('tests', 'test_shells', 'inputs', shell), 'rb') as F:
		if not wait_for_echo:
			child.send(F.read())
		else:
			for line in F:
				child.send(line)
				sleep(1)
				# TODO Implement something more smart

	output = child.read().decode('utf-8')
	child.close(force=True)

	return output


def postprocess_output(shell, output, test_root):
	pid_fname = os.path.join(test_root, '3rd', 'pid')

	is_pypy = platform.python_implementation() == 'PyPy'

	try:
		with open(pid_fname, 'r') as P:
			pid = P.read().strip()
	except IOError:
		pid = None
	hostname = socket.gethostname()
	user = os.environ['USER']

	REFS_RE = re.compile(r'^\[\d+ refs\]\n')
	IPYPY_DEANSI_RE = re.compile(r'\033(?:\[(?:\?\d+[lh]|[^a-zA-Z]+[a-ln-zA-Z])|[=>])')
	ZSH_HL_RE = re.compile(r'\033\[\?\d+[hl]')

	start_str = 'cd "$TEST_ROOT"/3rd'
	if shell == 'pdb':
		start_str = 'class Foo(object):'

	found_cd = False
	postprocessed = ""
	for line in output.split("\n"):
		line += "\n"
		if not found_cd:
			found_cd = (start_str in line)
			continue
		if 'true is the last line' in line:
			break
		line = line.translate({
			ord('\r'): None
		})
		if REFS_RE.match(line):
			continue
		line = line.replace(hostname, 'HOSTNAME')
		line = line.replace(user, 'USER')
		if pid is not None:
			line = line.replace(pid, 'PID')
		if shell == 'zsh':
			line = line.replace('\033[0m\033[23m\033[24m\033[J', '')
			line = ZSH_HL_RE.subn('', line)[0]
		elif shell == 'fish':
			res = ''
			try:
				while line.index('\033[0;'):
					start = line.index('\033[0;')
					end = line.index('\033[0m', start)
					res += line[start:end + 4] + '\n'
					line = line[end + 4:]
			except ValueError:
				pass
			line = res
		elif shell == 'tcsh':
			try:
				start = line.index('\033[0;')
				end = line.index(' ', start)
				line = line[start:end] + '\n'
			except ValueError:
				line = ''
		elif shell == 'mksh':
			# Output is different in travis: on my machine I see full
			# command, in travis it is truncated just after `true`.
			if line.startswith('[1] + Terminated'):
				line = '[1] + Terminated bash -c ...\n'
		elif shell == 'dash':
			# Position of this line is not stable: it may go both before and
			# after the next line
			if line.startswith('[1] + Terminated'):
				continue
		elif shell == 'ipython' and is_pypy:
			try:
				end_idx = line.rindex('\033[0m')
				try:
					idx = line[:end_idx].rindex('\033[1;1H')
				except ValueError:
					idx = line[:end_idx].rindex('\033[?25h')
				line = line[idx + len('\033[1;1H'):]
			except ValueError:
				pass
			try:
				data_end_idx = line.rindex('\033[1;1H')
				line = line[:data_end_idx] + '\n'
			except ValueError:
				pass
			if line == '\033[1;1H\n':
				continue
			was_empty = line == '\n'
			line = IPYPY_DEANSI_RE.subn('', line)[0]
			if line == '\n' and not was_empty:
				line = ''
		elif shell == 'rc':
			if line == 'read() failed: Connection reset by peer\n':
				line = ''
		elif shell == 'pdb':
			if is_pypy:
				if line == '\033[?1h\033=\033[?25l\033[1A\n':
					line = ''
				line = IPYPY_DEANSI_RE.subn('', line)[0]
				if line == '\n':
					line = ''
			if line.startswith(('>',)):
				line = ''
			elif line == '-> self.quitting = 1\n':
				line = '-> self.quitting = True\n'
			elif line == '\n':
				line = ''
			if line == '-> self.quitting = True\n':
				break
		postprocessed += line
	return postprocessed