#!/usr/bin/env python

from __future__ import unicode_literals

import os
import socket
import sys
import codecs


shell = sys.argv[1]
fname = os.path.join('tests', 'shell', shell + '.full.log')
new_fname = os.path.join('tests', 'shell', shell + '.log')
pid_fname = os.path.join('tests', 'shell', '3rd', 'pid')


with open(pid_fname, 'r') as P:
	pid = P.read().strip()
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
			W.write(line)
