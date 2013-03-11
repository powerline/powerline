# This module contains abstractions for the input stream. You don't have to
# looks further, there are no pretty code.

__all__ = ['Reader', 'ReaderError']

from .error import JSONError, Mark

import codecs
import re

try:
	from __builtin__ import unicode, unichr
except ImportError:
	unicode = str  # NOQA
	unichr = chr  # NOQA


class ReaderError(JSONError):
	def __init__(self, name, position, character, encoding, reason):
		self.name = name
		self.character = character
		self.position = position
		self.encoding = encoding
		self.reason = reason

	def __str__(self):
		if isinstance(self.character, bytes):
			return "'%s' codec can't decode byte #x%02x: %s\n"	\
					"  in \"%s\", position %d"	  \
					% (self.encoding, ord(self.character), self.reason,
							self.name, self.position)
		else:
			return "unacceptable character #x%04x: %s\n"	\
					"  in \"%s\", position %d"	  \
					% (self.character, self.reason,
							self.name, self.position)


class Reader(object):
	# Reader:
	# - determines the data encoding and converts it to a unicode string,
	# - checks if characters are in allowed range,
	# - adds '\0' to the end.

	# Reader accepts
	#  - a file-like object with its `read` method returning `str`,

	# Yeah, it's ugly and slow.
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
		self.name = getattr(stream, 'name', "<file>")
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

	def forward(self, length=1):
		if self.pointer + length + 1 >= len(self.buffer):
			self.update(length + 1)
		while length:
			ch = self.buffer[self.pointer]
			self.pointer += 1
			self.full_pointer += 1
			self.index += 1
			if ch == '\n':
				self.line += 1
				self.column = 0
			length -= 1

	def get_mark(self):
		return Mark(self.name, self.index, self.line, self.column,
				self.full_buffer, self.full_pointer)

	NON_PRINTABLE = re.compile('[^\t\n\x20-\x7E' + unichr(0x85) + (unichr(0xA0) + '-' + unichr(0xD7FF)) + (unichr(0xE000) + '-' + unichr(0xFFFD)) + ']')

	def check_printable(self, data):
		match = self.NON_PRINTABLE.search(data)
		if match:
			character = match.group()
			position = self.index + (len(self.buffer) - self.pointer) + match.start()
			raise ReaderError(self.name, position, ord(character), 'unicode', "special characters are not allowed")

	def update(self, length):
		if self.raw_buffer is None:
			return
		self.buffer = self.buffer[self.pointer:]
		self.pointer = 0
		while len(self.buffer) < length:
			if not self.eof:
				self.update_raw()
			try:
				data, converted = self.raw_decode(self.raw_buffer,
						'strict', self.eof)
			except UnicodeDecodeError as exc:
				character = self.raw_buffer[exc.start]
				position = self.stream_pointer - len(self.raw_buffer) + exc.start
				raise ReaderError(self.name, position, character, exc.encoding, exc.reason)
			self.check_printable(data)
			self.buffer += data
			self.full_buffer += data
			self.raw_buffer = self.raw_buffer[converted:]
			if self.eof:
				self.buffer += '\0'
				self.raw_buffer = None
				break

	def update_raw(self, size=4096):
		data = self.stream.read(size)
		if self.raw_buffer is None:
			self.raw_buffer = data
		else:
			self.raw_buffer += data
		self.stream_pointer += len(data)
		if not data:
			self.eof = True
