from sphinx.ext import autodoc
from sphinx.util.inspect import getargspec
from inspect import ArgSpec, formatargspec
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from itertools import count

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
		if isinstance(self.object, ThreadedSegment):
			args = ['interval']
			defaults = [getattr(self.object, 'interval', 1)]
			if self.object.update_first:
				args.append('update_first')
				defaults.append(True)
			methods = ['render', 'set_state']
			if isinstance(self.object, KwThreadedSegment):
				methods += ['key', 'render_one']

			for method in methods:
				if hasattr(self.object, method):
					# Note: on <python-2.6 it may return simple tuple, not 
					# ArgSpec instance.
					argspec = getargspec(getattr(self.object, method))
					for i, arg in zip(count(-1, -1), reversed(argspec.args)):
						if (arg == 'self' or
								(arg == 'segment_info' and
									getattr(self.object, 'powerline_requires_segment_info', None)) or
								(method == 'render_one' and -i == len(argspec.args)) or
								arg in args):
							continue
						if argspec.defaults and len(argspec.defaults) >= -i:
							default = argspec.defaults[i]
							defaults.append(default)
							args.append(arg)
						else:
							args.insert(0, arg)
			argspec = ArgSpec(args=args, varargs=None, keywords=None, defaults=tuple(defaults))
		else:
			if hasattr(self.object, 'powerline_origin'):
				obj = self.object.powerline_origin
			else:
				obj = self.object

			argspec = getargspec(obj)
			args = []
			defaults = []
			for i, arg in zip(count(-1, -1), reversed(argspec.args)):
				if (arg == 'segment_info' and getattr(self.object, 'powerline_requires_segment_info', None)):
					continue
				if argspec.defaults and len(argspec.defaults) >= -i:
					default = argspec.defaults[i]
					defaults.append(default)
					args.append(arg)
				else:
					args.insert(0, arg)
			argspec = ArgSpec(args=args, varargs=argspec.varargs, keywords=argspec.keywords, defaults=tuple(defaults))

		return formatargspec(*argspec, formatvalue=formatvalue).replace('\\', '\\\\')


def setup(app):
	autodoc.setup(app)
	app.add_autodocumenter(ThreadedDocumenter)
