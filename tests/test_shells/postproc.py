#!/usr/bin/env python

from __future__ import unicode_literals

import os
import socket
import sys
import codecs


test_type = sys.argv[1]
shell = sys.argv[2]
fname = os.path.join('tests', 'shell', shell + '.' + test_type + '.full.log')
new_fname = os.path.join('tests', 'shell', shell + '.' + test_type + '.log')
pid_fname = os.path.join('tests', 'shell', '3rd', 'pid')


try:
	with open(pid_fname, 'r') as P:
		pid = P.read().strip()
except IOError:
	pid = None
hostname = socket.gethostname()
user = os.environ['USER']

with codecs.open(fname, 'r', encoding='utf-8') as R:
	with codecs.open(new_fname, 'w', encoding='utf-8') as W:
		found_cd = False
		for line in (R if shell != 'fish' else R.read().split('\n')):
			if not found_cd:
				found_cd = ('cd tests/shell/3rd' in line)
				continue
			if 'true is the last line' in line:
				break
			line = line.translate({
				ord('\r'): None
			})
			line = line.replace(hostname, 'HOSTNAME')
			line = line.replace(user, 'USER')
			if pid is not None:
				line = line.replace(pid, 'PID')
			if shell == 'fish':
				try:
					start = line.index('\033[0;')
					end = line.index('\033[0m', start)
					line = line[start:end + 4] + '\n'
				except ValueError:
					line = ''
			elif shell == 'tcsh':
				try:
					start = line.index('\033[0;')
					end = line.index(' ', start)
					line = line[start:end] + '\033[0m\n'
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
			W.write(line)
