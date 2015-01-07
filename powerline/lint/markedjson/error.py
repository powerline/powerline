# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import re


NON_PRINTABLE_STR = (
	'[^'
	# ASCII control characters: 0x00-0x19
	+ '\t\n'           # Tab, newline: allowed ASCII control characters
	+ '\x20-\x7E'      # ASCII printable characters
	# Unicode control characters: 0x7F-0x9F
	+ '\u0085'         # Allowed unicode control character: next line character
	+ '\u00A0-\uD7FF'
	# Surrogate escapes: 0xD800-0xDFFF
	+ '\uE000-\uFFFD'
	+ ((
		'\uD800-\uDFFF'
	) if sys.maxunicode < 0x10FFFF else (
		'\U00010000-\U0010FFFF'
	))
	+ ']'
	+ ((
		# Paired surrogate escapes: allowed in UCS-2 builds as the only way to 
		# represent characters above 0xFFFF. Only paired variant is allowed.
		'|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]'
		+ '|[\uD800-\uDBFF](?![\uDC00-\uDFFF])'
	) if sys.maxunicode < 0x10FFFF else (
		''
	))
)
NON_PRINTABLE_RE = re.compile(NON_PRINTABLE_STR)


def repl(s):
	return '<x%04x>' % ord(s.group())


def strtrans(s):
	return NON_PRINTABLE_RE.sub(repl, s.replace('\t', '>---'))


class Mark:
	def __init__(self, name, line, column, buffer, pointer, old_mark=None, merged_marks=None):
		self.name = name
		self.line = line
		self.column = column
		self.buffer = buffer
		self.pointer = pointer
		self.old_mark = old_mark
		self.merged_marks = merged_marks or []

	def copy(self):
		return Mark(self.name, self.line, self.column, self.buffer, self.pointer, self.old_mark, self.merged_marks[:])

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
		return (
			' ' * indent + head + ''.join(snippet) + tail + '\n'
			+ ' ' * (indent + len(head) + len(snippet[0])) + '^'
		)

	def advance_string(self, diff):
		ret = self.copy()
		# FIXME Currently does not work properly with escaped strings.
		ret.column += diff
		ret.pointer += diff
		return ret

	def set_old_mark(self, old_mark):
		if self is old_mark:
			return
		checked_marks = set([id(self)])
		older_mark = old_mark
		while True:
			if id(older_mark) in checked_marks:
				raise ValueError('Trying to set recursive marks')
			checked_marks.add(id(older_mark))
			older_mark = older_mark.old_mark
			if not older_mark:
				break
		self.old_mark = old_mark

	def set_merged_mark(self, merged_mark):
		self.merged_marks.append(merged_mark)

	def to_string(self, indent=0, head_text='in ', add_snippet=True):
		mark = self
		where = ''
		processed_marks = set()
		while mark:
			indentstr = ' ' * indent
			where += ('%s  %s"%s", line %d, column %d' % (
				indentstr, head_text, mark.name, mark.line + 1, mark.column + 1))
			if add_snippet:
				snippet = mark.get_snippet(indent=(indent + 4))
				if snippet:
					where += ':\n' + snippet
			if mark.merged_marks:
				where += '\n' + indentstr + '  with additionally merged\n'
				where += mark.merged_marks[0].to_string(indent + 4, head_text='', add_snippet=False)
				for mmark in mark.merged_marks[1:]:
					where += '\n' + indentstr + '  and\n'
					where += mmark.to_string(indent + 4, head_text='', add_snippet=False)
			if add_snippet:
				processed_marks.add(id(mark))
				if mark.old_mark:
					where += '\n' + indentstr + '  which replaced value\n'
					indent += 4
			mark = mark.old_mark
			if id(mark) in processed_marks:
				raise ValueError('Trying to dump recursive mark')
		if type(where) is str:
			return where
		else:
			return where.encode('utf-8')

	def __str__(self):
		return self.to_string()


def echoerr(*args, **kwargs):
	stream = kwargs.pop('stream', sys.stderr)
	stream.write('\n')
	stream.write(format_error(*args, **kwargs) + '\n')


def format_error(context=None, context_mark=None, problem=None, problem_mark=None, note=None):
	lines = []
	if context is not None:
		lines.append(context)
	if (
		context_mark is not None
		and (
			problem is None or problem_mark is None
			or context_mark.name != problem_mark.name
			or context_mark.line != problem_mark.line
			or context_mark.column != problem_mark.column
		)
	):
		lines.append(str(context_mark))
	if problem is not None:
		lines.append(problem)
	if problem_mark is not None:
		lines.append(str(problem_mark))
	if note is not None:
		lines.append(note)
	return '\n'.join(lines)


class MarkedError(Exception):
	def __init__(self, context=None, context_mark=None, problem=None, problem_mark=None, note=None):
		Exception.__init__(self, format_error(context, context_mark, problem, problem_mark, note))


class EchoErr(object):
	__slots__ = ('echoerr', 'logger',)

	def __init__(self, echoerr, logger):
		self.echoerr = echoerr
		self.logger = logger

	def __call__(self, *args, **kwargs):
		self.echoerr(*args, **kwargs)


class DelayedEchoErr(EchoErr):
	__slots__ = ('echoerr', 'logger', 'errs')

	def __init__(self, echoerr):
		super(DelayedEchoErr, self).__init__(echoerr, echoerr.logger)
		self.errs = []

	def __call__(self, *args, **kwargs):
		self.errs.append((args, kwargs))

	def echo_all(self):
		for args, kwargs in self.errs:
			self.echoerr(*args, **kwargs)

	def __nonzero__(self):
		return not not self.errs

	__bool__ = __nonzero__
