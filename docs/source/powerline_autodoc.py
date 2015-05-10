# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

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


class Repr(object):
	def __init__(self, repr_contents):
		self.repr_contents = repr_contents

	def __repr__(self):
		return '<{0}>'.format(self.repr_contents)


class EnvironDocumenter(autodoc.AttributeDocumenter):
	@classmethod
	def can_document_member(cls, member, membername, isattr, parent):
		if type(member) is dict and member.get('environ') is os.environ:
			return True
		else:
			return False

	def import_object(self, *args, **kwargs):
		ret = super(EnvironDocumenter, self).import_object(*args, **kwargs)
		if not ret:
			return ret
		self.object = self.object.copy()
		if 'home' in self.object:
			self.object.update(home=Repr('home directory'))
		self.object.update(environ=Repr('environ dictionary'))
		return True


def setup(app):
	autodoc.setup(app)
	app.add_autodocumenter(ThreadedDocumenter)
	app.add_autodocumenter(EnvironDocumenter)
