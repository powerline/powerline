# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import threading

from time import sleep
from itertools import groupby

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
		sleep(0.5)
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

	def resize(self, rows, cols):
		with self.child_lock:
			self.rows = rows
			self.cols = cols
			self.child.setwinsize(rows, cols)
			self.vterm.resize(rows, cols)

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

	def get_highlighted_text(self, text, attrs, default_props=()):
		ret = []
		new_attrs = attrs.copy()
		for cell_properties, segment_text in text:
			segment_text = segment_text.translate({'{': '{{', '}': '}}'})
			if cell_properties not in new_attrs:
				new_attrs[cell_properties] = len(new_attrs) + 1
			props_name = new_attrs[cell_properties]
			if props_name in default_props:
				ret.append(segment_text)
			else:
				ret.append('{' + str(props_name) + ':' + segment_text + '}')
		return ''.join(ret), new_attrs

	def get_row(self, row, attrs, default_props=()):
		with self.lock:
			return self.get_highlighted_text((
				(key, ''.join((cell.text for cell in subline)))
				for key, subline in groupby((
					self.vterm.vtscreen[row, col] for col in range(self.cols)
				), lambda cell: cell.cell_properties_key)
			), attrs, default_props)

	def get_screen(self, attrs, default_props=()):
		lines = []
		for row in range(self.rows):
			line, attrs = self.get_row(row, attrs, default_props)
			lines.append(line)
		return '\n'.join(lines), attrs
