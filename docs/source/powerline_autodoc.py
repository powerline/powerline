from sphinx.ext import autodoc
from sphinx.util.inspect import getargspec
from inspect import ArgSpec, getargspec, formatargspec
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from itertools import count


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
									getattr(self.object, 'requires_powerline_segment_info', None)) or
								(method == 'render_one' and -i == len(argspec.args))):
							continue
						if argspec.defaults and len(argspec.defaults) >= -i:
							default = argspec.defaults[i]
							defaults.append(default)
							args.append(arg)
						else:
							args.insert(0, arg)
			argspec = ArgSpec(args=args, varargs=None, keywords=None, defaults=tuple(defaults))
		else:
			argspec = getargspec(self.object)
			args = argspec.args
			defaults = argspec.defaults
			if args and args[0] == 'segment_info' and getattr(self.object, 'requires_powerline_segment_info', None):
				args = args[1:]
				if defaults and len(defaults) > len(args):
					defaults = defaults[1:]
			argspec = ArgSpec(args=args, varargs=argspec.varargs, keywords=argspec.keywords, defaults=defaults)

		return formatargspec(*argspec).replace('\\', '\\\\')


def setup(app):
	autodoc.setup(app)
	app.add_autodocumenter(ThreadedDocumenter)
