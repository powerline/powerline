#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import socket
import sys
import codecs
import platform
import re


test_root = os.environ['TEST_ROOT']
test_type = sys.argv[1]
test_client = sys.argv[2]
shell = sys.argv[3]
fname = os.path.join(test_root, '.'.join((shell, test_type, test_client, 'full.log')))
new_fname = os.path.join(test_root, '.'.join((shell, test_type, test_client, 'log')))
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

with codecs.open(fname, 'r', encoding='utf-8') as R:
	with codecs.open(new_fname, 'w', encoding='utf-8') as W:
		found_cd = False
		i = -1
		for line in (R if shell != 'fish' else R.read().split('\n')):
			i += 1
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
			W.write(line)
