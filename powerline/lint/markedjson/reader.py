# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import codecs

from powerline.lint.markedjson.error import MarkedError, Mark, NON_PRINTABLE_RE
from powerline.lib.unicode import unicode


# This module contains abstractions for the input stream. You don’t have to
# looks further, there are no pretty code.


class ReaderError(MarkedError):
	pass


class Reader(object):
	# Reader:
	# - determines the data encoding and converts it to a unicode string,
	# - checks if characters are in allowed range,
	# - adds '\0' to the end.

	# Reader accepts
	#  - a file-like object with its `read` method returning `str`,

	# Yeah, it’s ugly and slow.
	def __init__(self, stream):
		self.name = None
		self.stream = None
		self.stream_pointer = 0
		self.eof = True
		self.buffer = ''
		self.pointer = 0
		self.full_buffer = unicode('')
		self.full_pointer = 0
		self.raw_buffer = None
		self.raw_decode = codecs.utf_8_decode
		self.encoding = 'utf-8'
		self.index = 0
		self.line = 0
		self.column = 0

		self.stream = stream
		self.name = getattr(stream, 'name', '<file>')
		self.eof = False
		self.raw_buffer = None

		while not self.eof and (self.raw_buffer is None or len(self.raw_buffer) < 2):
			self.update_raw()
		self.update(1)

	def peek(self, index=0):
		try:
			return self.buffer[self.pointer + index]
		except IndexError:
			self.update(index + 1)
			return self.buffer[self.pointer + index]

	def prefix(self, length=1):
		if self.pointer + length >= len(self.buffer):
			self.update(length)
		return self.buffer[self.pointer:self.pointer + length]

	def update_pointer(self, length):
		while length:
			ch = self.buffer[self.pointer]
			self.pointer += 1
			self.full_pointer += 1
			self.index += 1
			if ch == '\n':
				self.line += 1
				self.column = 0
			else:
				self.column += 1
			length -= 1

	def forward(self, length=1):
		if self.pointer + length + 1 >= len(self.buffer):
			self.update(length + 1)
		self.update_pointer(length)

	def get_mark(self):
		return Mark(self.name, self.line, self.column, self.full_buffer, self.full_pointer)

	def check_printable(self, data):
		match = NON_PRINTABLE_RE.search(data)
		if match:
			self.update_pointer(match.start())
			raise ReaderError(
				'while reading from stream', None,
				'found special characters which are not allowed',
				Mark(self.name, self.line, self.column, self.full_buffer, self.full_pointer)
			)

	def update(self, length):
		if self.raw_buffer is None:
			return
		self.buffer = self.buffer[self.pointer:]
		self.pointer = 0
		while len(self.buffer) < length:
			if not self.eof:
				self.update_raw()
			try:
				data, converted = self.raw_decode(self.raw_buffer, 'strict', self.eof)
			except UnicodeDecodeError as exc:
				character = self.raw_buffer[exc.start]
				position = self.stream_pointer - len(self.raw_buffer) + exc.start
				data, converted = self.raw_decode(self.raw_buffer[:exc.start], 'strict', self.eof)
				self.buffer += data
				self.full_buffer += data + '<' + str(ord(character)) + '>'
				self.raw_buffer = self.raw_buffer[converted:]
				self.update_pointer(exc.start - 1)
				raise ReaderError(
					'while reading from stream', None,
					'found character #x%04x that cannot be decoded by UTF-8 codec' % ord(character),
					Mark(self.name, self.line, self.column, self.full_buffer, position)
				)
			self.buffer += data
			self.full_buffer += data
			self.raw_buffer = self.raw_buffer[converted:]
			self.check_printable(data)
			if self.eof:
				self.buffer += '\0'
				self.raw_buffer = None
				break

	def update_raw(self, size=-1):
		# Was size=4096
		assert(size < 0)
		# WARNING: reading the whole stream at once. To change this behaviour to 
		# former reading N characters at once one must make sure that reading 
		# never ends at partial unicode character.
		data = self.stream.read(size)
		if self.raw_buffer is None:
			self.raw_buffer = data
		else:
			self.raw_buffer += data
		self.stream_pointer += len(data)
		if not data:
			self.eof = True
