# vim:fileencoding=utf-8:noet
from sphinx.ext import autodoc
from inspect import formatargspec
from powerline.lint.inspect import getconfigargspec
from powerline.lib.threaded import ThreadedSegment

try:
	from __builtin__ import unicode
except ImportError:
	unicode = lambda s, enc: s  # NOQA


def formatvalue(val):
	if type(val) is str:
		return '="' + unicode(val, 'utf-8').replace('"', '\\"').replace('\\', '\\\\') + '"'
	else:
		return '=' + repr(val)


class ThreadedDocumenter(autodoc.FunctionDocumenter):
	'''Specialized documenter subclass for ThreadedSegment subclasses.'''
	@classmethod
	def can_document_member(cls, member, membername, isattr, parent):
		return (isinstance(member, ThreadedSegment) or
			super(ThreadedDocumenter, cls).can_document_member(member, membername, isattr, parent))

	def format_args(self):
		argspec = getconfigargspec(self.object)
		return formatargspec(*argspec, formatvalue=formatvalue).replace('\\', '\\\\')


def setup(app):
	autodoc.setup(app)
	app.add_autodocumenter(ThreadedDocumenter)
