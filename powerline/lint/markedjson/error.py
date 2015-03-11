# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import re

from powerline.lib.encoding import get_preferred_output_encoding


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
		return where

	if sys.version_info < (3,):
		def __str__(self):
			return self.to_string().encode('utf-8')

		def __unicode__(self):
			return self.to_string()
	else:
		def __str__(self):
			return self.to_string()

	def __eq__(self, other):
		return self is other or (
			self.name == other.name
			and self.line == other.line
			and self.column == other.column
		)


if sys.version_info < (3,):
	def echoerr(**kwargs):
		stream = kwargs.pop('stream', sys.stderr)
		stream.write('\n')
		stream.write((format_error(**kwargs) + '\n').encode(get_preferred_output_encoding()))
else:
	def echoerr(**kwargs):
		stream = kwargs.pop('stream', sys.stderr)
		stream.write('\n')
		stream.write(format_error(**kwargs) + '\n')


def format_error(context=None, context_mark=None, problem=None, problem_mark=None, note=None, indent=0):
	lines = []
	indentstr = ' ' * indent
	if context is not None:
		lines.append(indentstr + context)
	if (
		context_mark is not None
		and (
			problem is None or problem_mark is None
			or context_mark != problem_mark
		)
	):
		lines.append(context_mark.to_string(indent=indent))
	if problem is not None:
		lines.append(indentstr + problem)
	if problem_mark is not None:
		lines.append(problem_mark.to_string(indent=indent))
	if note is not None:
		lines.append(indentstr + note)
	return '\n'.join(lines)


class MarkedError(Exception):
	def __init__(self, context=None, context_mark=None, problem=None, problem_mark=None, note=None):
		Exception.__init__(self, format_error(context, context_mark, problem, problem_mark, note))


class EchoErr(object):
	__slots__ = ('echoerr', 'logger', 'indent')

	def __init__(self, echoerr, logger, indent=0):
		self.echoerr = echoerr
		self.logger = logger
		self.indent = indent

	def __call__(self, **kwargs):
		kwargs = kwargs.copy()
		kwargs.setdefault('indent', self.indent)
		self.echoerr(**kwargs)


class DelayedEchoErr(EchoErr):
	__slots__ = ('echoerr', 'logger', 'errs', 'message', 'separator_message', 'indent', 'indent_shift')

	def __init__(self, echoerr, message='', separator_message=''):
		super(DelayedEchoErr, self).__init__(echoerr, echoerr.logger)
		self.errs = [[]]
		self.message = message
		self.separator_message = separator_message
		self.indent_shift = (4 if message or separator_message else 0)
		self.indent = echoerr.indent + self.indent_shift

	def __call__(self, **kwargs):
		kwargs = kwargs.copy()
		kwargs['indent'] = kwargs.get('indent', 0) + self.indent
		self.errs[-1].append(kwargs)

	def next_variant(self):
		self.errs.append([])

	def echo_all(self):
		if self.message:
			self.echoerr(problem=self.message, indent=(self.indent - self.indent_shift))
		for variant in self.errs:
			if not variant:
				continue
			if self.separator_message and variant is not self.errs[0]:
				self.echoerr(problem=self.separator_message, indent=(self.indent - self.indent_shift))
			for kwargs in variant:
				self.echoerr(**kwargs)

	def __nonzero__(self):
		return not not self.errs

	__bool__ = __nonzero__
