# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import subprocess
import re
import tempfile


# Copy of the Lib/ctypes/util.py from 3.4 branch of Python, commit 
# bb67b810aac0a56a1ae2d0e51d8030a8f59fae13. Everything, but linux-related stuff 
# was removed (this module is used solely for inotify).

def _findLib_gcc(name):
	expr = r'[^\(\)\s]*lib%s\.[^\(\)\s]*' % re.escape(name)
	fdout, ccout = tempfile.mkstemp()
	os.close(fdout)
	cmd = (
		'if type gcc >/dev/null 2>&1; then CC=gcc; elif type cc >/dev/null 2>&1; then CC=cc;else exit 10; fi;'
		'LANG=C LC_ALL=C $CC -Wl,-t -o ' + ccout + ' 2>&1 -l' + name
	)
	try:
		f = os.popen(cmd)
		try:
			trace = f.read()
		finally:
			rv = f.close()
	finally:
		try:
			os.unlink(ccout)
		except FileNotFoundError:
			pass
	if rv == 10:
		raise OSError('gcc or cc command not found')
	res = re.search(expr, trace)
	if not res:
		return None
	return res.group(0)


def _get_soname(f):
	# assuming GNU binutils / ELF
	if not f:
		return None
	cmd = (
		'if ! type objdump >/dev/null 2>&1; then exit 10; fi;'
		'objdump -p -j .dynamic 2>/dev/null ' + f
	)
	f = os.popen(cmd)
	try:
		dump = f.read()
	finally:
		rv = f.close()
	if rv == 10:
		raise OSError('objdump command not found')
	res = re.search(r'\sSONAME\s+([^\s]+)', dump)
	if not res:
		return None
	return res.group(1)


def _findSoname_ldconfig(name):
	import struct
	machine = subprocess.check_output(['uname', '-m'])[:-1]
	if struct.calcsize('l') == 4:
		machine += '-32'
	else:
		machine += '-64'
	mach_map = {
		'x86_64-64': 'libc6,x86-64',
		'ppc64-64': 'libc6,64bit',
		'sparc64-64': 'libc6,64bit',
		's390x-64': 'libc6,64bit',
		'ia64-64': 'libc6,IA-64',
	}
	abi_type = mach_map.get(machine, 'libc6')

	# XXX assuming GLIBC's ldconfig (with option -p)
	regex = '\s+(lib%s\.[^\s]+)\s+\(%s' % (re.escape(name), abi_type)
	try:
		p = subprocess.Popen(['/sbin/ldconfig', '-p'],
		                     stdin=subprocess.PIPE,
		                     stderr=subprocess.PIPE,
		                     stdout=subprocess.PIPE,
		                     env={'LC_ALL': 'C', 'LANG': 'C'})
		try:
			res = re.search(regex, p.stdout.read())
			if res:
				return res.group(1)
		finally:
			p.terminate()
	except OSError:
		pass


def find_library(name):
	return _findSoname_ldconfig(name) or _get_soname(_findLib_gcc(name))
