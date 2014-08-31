# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from inspect import formatargspec

from sphinx.ext import autodoc

from powerline.lint.inspect import getconfigargspec
from powerline.segments import Segment
from powerline.lib.unicode import unicode


def formatvalue(val):
	if type(val) is str:
		return '="' + unicode(val, 'utf-8').replace('"', '\\"').replace('\\', '\\\\') + '"'
	else:
		return '=' + repr(val)


class ThreadedDocumenter(autodoc.FunctionDocumenter):
	'''Specialized documenter subclass for ThreadedSegment subclasses.'''
	@classmethod
	def can_document_member(cls, member, membername, isattr, parent):
		return (isinstance(member, Segment) or
			super(ThreadedDocumenter, cls).can_document_member(member, membername, isattr, parent))

	def format_args(self):
		argspec = getconfigargspec(self.object)
		return formatargspec(*argspec, formatvalue=formatvalue).replace('\\', '\\\\')


def setup(app):
	autodoc.setup(app)
	app.add_autodocumenter(ThreadedDocumenter)
