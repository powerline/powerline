# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import threading

from time import sleep
from collections import namedtuple

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


def cpk_to_shesc(cpk):
	'''Convert one cell_properties_key item to shell escape sequence

	:param tests.lib.vterm.VTermScreenCell.cell_properties_key cpk:
		Item to convert.

	:return:
		String, shell escape sequence usable in terminals that are able to parse 
		true color escape sequences::

			\e[38;2;R;G;B;48;2;R;G;B{other attributes}m
	'''
	fg, bg, bold, underline, italic = cpk
	return('\x1b[38;2;{0};48;2;{1}{bold}{underline}{italic}m'.format(
		';'.join((str(i) for i in fg)),
		';'.join((str(i) for i in bg)),
		bold=(';1' if bold else ''),
		underline=(';4' if underline else ''),
		italic=(';3' if italic else ''),
	))


ColorKey = namedtuple('ColorKey', (
	'fg', 'bg', 'bold', 'underline', 'italic'
))
ColoredText = namedtuple('ColoredText', (
	'cell_properties_key', 'text'
))


def coltext_to_shesc(coltext):
	return ''.join((
		(lambda ctext: ('{0}{1}\x1b[m'.format(
			cpk_to_shesc(ctext.cell_properties_key),
			ctext.text
		)))(i if hasattr(i, 'cell_properties_key') else ColoredText(ColorKey(*i[0]), i[1]))
		for i in coltext
	))
