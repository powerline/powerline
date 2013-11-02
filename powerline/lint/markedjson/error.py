__all__ = ['Mark', 'MarkedError', 'echoerr', 'NON_PRINTABLE']


import sys
import re

try:
	from __builtin__ import unichr
except ImportError:
	unichr = chr  # NOQA


NON_PRINTABLE = re.compile('[^\t\n\x20-\x7E' + unichr(0x85) + (unichr(0xA0) + '-' + unichr(0xD7FF)) + (unichr(0xE000) + '-' + unichr(0xFFFD)) + ']')


def repl(s):
	return '<x%04x>' % ord(s.group())


def strtrans(s):
	return NON_PRINTABLE.sub(repl, s.replace('\t', '>---'))


class Mark:
	def __init__(self, name, line, column, buffer, pointer):
		self.name = name
		self.line = line
		self.column = column
		self.buffer = buffer
		self.pointer = pointer

	def copy(self):
		return Mark(self.name, self.line, self.column, self.buffer, self.pointer)

	def get_snippet(self, indent=4, max_length=75):
		if self.buffer is None:
			return None
		head = ''
		start = self.pointer
		while start > 0 and self.buffer[start - 1] not in '\0\n':
			start -= 1
			if self.pointer - start > max_length / 2 - 1:
				head = ' ... '
				start += 5
				break
		tail = ''
		end = self.pointer
		while end < len(self.buffer) and self.buffer[end] not in '\0\n':
			end += 1
			if end - self.pointer > max_length / 2 - 1:
				tail = ' ... '
				end -= 5
				break
		snippet = [self.buffer[start:self.pointer], self.buffer[self.pointer], self.buffer[self.pointer + 1:end]]
		snippet = [strtrans(s) for s in snippet]
		return (' ' * indent + head + ''.join(snippet) + tail + '\n'
				+ ' ' * (indent + len(head) + len(snippet[0])) + '^')

	def __str__(self):
		snippet = self.get_snippet()
		where = ("  in \"%s\", line %d, column %d"
				% (self.name, self.line + 1, self.column + 1))
		if snippet is not None:
			where += ":\n" + snippet
		if type(where) is str:
			return where
		else:
			return where.encode('utf-8')


def echoerr(*args, **kwargs):
	sys.stderr.write('\n')
	sys.stderr.write(format_error(*args, **kwargs) + '\n')


def format_error(context=None, context_mark=None, problem=None, problem_mark=None, note=None):
	lines = []
	if context is not None:
		lines.append(context)
	if context_mark is not None  \
		and (problem is None or problem_mark is None
				or context_mark.name != problem_mark.name
				or context_mark.line != problem_mark.line
				or context_mark.column != problem_mark.column):
		lines.append(str(context_mark))
	if problem is not None:
		lines.append(problem)
	if problem_mark is not None:
		lines.append(str(problem_mark))
	if note is not None:
		lines.append(note)
	return '\n'.join(lines)


class MarkedError(Exception):
	def __init__(self, context=None, context_mark=None,
			problem=None, problem_mark=None, note=None):
		Exception.__init__(self, format_error(context, context_mark, problem,
										problem_mark, note))
