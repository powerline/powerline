# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import threading
import logging

from time import sleep
from collections import namedtuple
from itertools import groupby
from io import BytesIO

import pexpect

from powerline.lib.monotonic import monotonic

from tests.lib.vterm import VTerm


logger = logging.getLogger('terminal')


class ExpectProcess(threading.Thread):
	def __init__(self, lib, rows, cols, cmd, args, cwd=None, env=None, init_input=''):
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
		self.child_lock = threading.RLock()
		self.init_input = init_input

	def read_child(self, timeout=0):
		status = None
		try:
			with self.child_lock:
				s = self.child.read_nonblocking(size=1024, timeout=timeout)
				status = self.child.status
		except pexpect.TIMEOUT:
			return True, status, b''
		except pexpect.EOF:
			return False, status, b''
		except ValueError:  # I/O operation on closed file
			return False, status, b''
		else:
			return True, status, s

	def run(self):
		with self.child_lock:
			child = pexpect.spawn(self.cmd, self.args, cwd=self.cwd, env=self.env)
			sleep(0.5)
			child.setwinsize(self.rows, self.cols)
			sleep(0.5)
			self.child = child
		status = None
		if self.init_input:
			self.write(self.init_input)
			s = True
			while s:
				cont, status, s = self.read_child(0.1)
				if not cont:
					break
				with self.lock:
					self.buffer.append(s)
		while status is None:
			cont, status, s = self.read_child()
			if not cont:
				break
			with self.child_lock:
				self.vterm.push(s)
			with self.lock:
				self.buffer.append(s)

	def start(self, *args, **kwargs):
		super(ExpectProcess, self).start(*args, **kwargs)
		sleep(1)

	def resize(self, rows, cols):
		with self.child_lock:
			self.rows = rows
			self.cols = cols
			self.child.setwinsize(rows, cols)
			self.vterm.resize(rows, cols)

	def __getitem__(self, position):
		row, col = position
		with self.child_lock:
			if col is Ellipsis and row is Ellipsis:
				return (
					self[row, col]
					for row in range(self.rows)  # NOQA
				)
			elif col is Ellipsis:
				return (
					self[row, col]
					for col in range(self.cols)  # NOQA
				)
			elif row is Ellipsis:
				return (
					self[row, col]
					for row in range(self.rows)  # NOQA
				)
			else:
				return self.vterm.vtscreen[row, col]

	def read(self):
		with self.lock:
			ret = b''.join(self.buffer)
			del self.buffer[:]
			return ret

	def waitfor(self, regex, timeout=1):
		buf = BytesIO(self.read())
		if regex.search(buf.getvalue()):
			return buf.getvalue()
		start_time = monotonic()
		while monotonic() - start_time < timeout:
			sleep(0.1)
			buf.write(self.read())
			if regex.search(buf.getvalue()):
				return buf.getvalue()
		with self.lock:
			self.buffer.append(buf.getvalue())
		raise ValueError('Timed out')

	def send(self, data):
		with self.child_lock:
			self.child.send(data)

	write = send

	def row(self, row):
		return coltext_join(self[row, Ellipsis])

	def close(self):
		with self.child_lock:
			if hasattr(self, 'child'):
				try:
					self.child.close(force=True)
				except pexpect.ExceptionPexpect as e:
					logging.exception('Exception %r', e)


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


def coltext_join(coltext):
	ret = tuple((
		(cpk, ''.join((i.text or ' ' for i in cell_group)))
		for cpk, cell_group in groupby(coltext, lambda i: i.cell_properties_key)
	))
	if ret == ((
		(
			(240, 240, 240),
			(0, 0, 0),
			0, 0, 0
		),
		' ' * len(ret[0][1])
	),):
		return ()
	return ret


def coltext_to_shesc(coltext):
	return ''.join((
		(lambda ctext: ('{0}{1}\x1b[m'.format(
			cpk_to_shesc(ctext.cell_properties_key),
			ctext.text
		)))(i if hasattr(i, 'cell_properties_key') else ColoredText(ColorKey(*i[0]), i[1]))
		for i in coltext
	))
