# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import threading

from time import sleep

import pexpect

from tests.lib.vterm import VTerm


class ExpectProcess(threading.Thread):
	def __init__(self, lib, rows, cols, cmd, args, cwd=None, env=None):
		super(ExpectProcess, self).__init__()
		self.vterm = VTerm(lib, rows, cols)
		self.lock = threading.Lock()
		self.rows = rows
		self.cols = cols
		self.cmd = cmd
		self.args = args
		self.cwd = cwd
		self.env = env
		self.buffer = []
		self.child_lock = threading.Lock()

	def run(self):
		child = pexpect.spawn(self.cmd, self.args, cwd=self.cwd, env=self.env)
		sleep(0.5)
		child.setwinsize(self.rows, self.cols)
		self.child = child
		status = None
		while status is None:
			try:
				with self.child_lock:
					s = child.read_nonblocking(size=1024, timeout=0)
					status = child.status
			except pexpect.TIMEOUT:
				pass
			except pexpect.EOF:
				break
			else:
				with self.lock:
					self.vterm.push(s)
					self.buffer.append(s)

	def __getitem__(self, position):
		with self.lock:
			return self.vterm.vtscreen[position]

	def read(self):
		with self.lock:
			ret = b''.join(self.buffer)
			del self.buffer[:]
			return ret

	def send(self, data):
		with self.child_lock:
			self.child.send(data)
