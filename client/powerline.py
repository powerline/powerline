#!/usr/bin/env python
# vim:fileencoding=utf-8:noet

from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import socket
import os
import errno

if len(sys.argv) < 2:
	print('Must provide at least one argument.', file=sys.stderr)
	raise SystemExit(1)

platform = sys.platform.lower()
use_filesystem = 'darwin' in platform
# use_filesystem = True
del platform

address = ('/tmp/powerline-ipc-%d' if use_filesystem else '\0powerline-ipc-%d') % os.getuid()

sock = socket.socket(family=socket.AF_UNIX)


def eintr_retry_call(func, *args, **kwargs):
	while True:
		try:
			return func(*args, **kwargs)
		except EnvironmentError as e:
			if getattr(e, 'errno', None) == errno.EINTR:
				continue
			raise

try:
	eintr_retry_call(sock.connect, address)
except Exception:
	# Run the powerline renderer
	args = ['powerline-render'] + sys.argv[1:]
	os.execvp('powerline-render', args)

fenc = sys.getfilesystemencoding() or 'utf-8'
if fenc == 'ascii':
	fenc = 'utf-8'

args = [bytes('%x' % (len(sys.argv) - 1))]
args.extend((x.encode(fenc) if isinstance(x, type('')) else x for x in sys.argv[1:]))

try:
	cwd = os.getcwd()
except EnvironmentError:
	pass
else:
	if isinstance(cwd, type('')):
		cwd = cwd.encode(fenc)
	args.append(cwd)


env = (k + b'=' + v for k, v in os.environ.items())
env = (x if isinstance(x, bytes) else x.encode(fenc, 'replace') for x in env)
args.extend(env)

EOF = b'\0\0'

for a in args:
	eintr_retry_call(sock.sendall, a + b'\0')

eintr_retry_call(sock.sendall, EOF)

received = []
while True:
	r = sock.recv(4096)
	if not r:
		break
	received.append(r)

sock.close()

sys.stdout.write(b''.join(received))
