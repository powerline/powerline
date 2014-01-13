#!/usr/bin/env python

from __future__ import unicode_literals

import os
import socket
import sys
import codecs


fname = sys.argv[1]
new_fname = fname + '.new'
pid_fname = 'tests/shell/3rd/pid'

with open(pid_fname, 'r') as P:
	pid = P.read().strip()
hostname = socket.gethostname()
user = os.environ['USER']

with codecs.open(fname, 'r', encoding='utf-8') as R:
	with codecs.open(new_fname, 'w', encoding='utf-8') as W:
		found_cd = False
		for line in R:
			if not found_cd:
				found_cd = ('cd tests/shell/3rd' in line)
				continue
			line = line.replace(pid, 'PID')
			line = line.replace(hostname, 'HOSTNAME')
			line = line.replace(user, 'USER')
			W.write(line)

os.rename(new_fname, fname)
