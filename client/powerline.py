#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import socket
import errno
import os

try:
	from posix import environ
except ImportError:
	from os import environ

# XXX Hack for importing powerline modules to work.
sys.path.pop(0)

try:
	from powerline.lib.encoding import get_preferred_output_encoding
except ImportError:
	sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__)))))
	from powerline.lib.encoding import get_preferred_output_encoding


if len(sys.argv) < 2:
	print('Must provide at least one argument.', file=sys.stderr)
	raise SystemExit(1)

use_filesystem = not sys.platform.lower().startswith('linux')

if sys.argv[1] == '--socket':
	address = sys.argv[2]
	if not use_filesystem:
		address = '\0' + address
	del sys.argv[1:3]
else:
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

fenc = get_preferred_output_encoding()


def tobytes(s):
	if isinstance(s, bytes):
		return s
	else:
		return s.encode(fenc)


args = [tobytes('%x' % (len(sys.argv) - 1))]
args.extend((tobytes(s) for s in sys.argv[1:]))


try:
	cwd = os.getcwd()
except EnvironmentError:
	pass
else:
	if not isinstance(cwd, bytes):
		cwd = cwd.encode(fenc)
	args.append(cwd)


args.extend((tobytes(k) + b'=' + tobytes(v) for k, v in environ.items()))

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

if sys.version_info < (3,):
	sys.stdout.write(b''.join(received))
else:
	sys.stdout.buffer.write(b''.join(received))
