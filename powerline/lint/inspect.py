# vim:fileencoding=utf-8:noet
from __future__ import absolute_import
from inspect import ArgSpec, getargspec
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from itertools import count

def getconfigargspec(obj):
	if isinstance(obj, ThreadedSegment):
		args = ['interval']
		defaults = [getattr(obj, 'interval', 1)]
		if obj.update_first:
			args.append('update_first')
			defaults.append(True)
		methods = ['render', 'set_state']
		if isinstance(obj, KwThreadedSegment):
			methods += ['key', 'render_one']

		for method in methods:
			if hasattr(obj, method):
				# Note: on <python-2.6 it may return simple tuple, not 
				# ArgSpec instance.
				argspec = getargspec(getattr(obj, method))
				for i, arg in zip(count(1), reversed(argspec.args)):
					if (arg == 'self' or
							(arg == 'segment_info' and
								getattr(obj, 'powerline_requires_segment_info', None)) or
							(arg == 'pl') or
							(method.startswith('render') and (1 if argspec.args[0] == 'self' else 0) + i == len(argspec.args)) or
							arg in args):
						continue
					if argspec.defaults and len(argspec.defaults) >= i:
						default = argspec.defaults[-i]
						defaults.append(default)
						args.append(arg)
					else:
						args.insert(0, arg)
		argspec = ArgSpec(args=args, varargs=None, keywords=None, defaults=tuple(defaults))
	else:
		if hasattr(obj, 'powerline_origin'):
			obj = obj.powerline_origin
		else:
			obj = obj

		argspec = getargspec(obj)
		args = []
		defaults = []
		for i, arg in zip(count(1), reversed(argspec.args)):
			if ((arg == 'segment_info' and getattr(obj, 'powerline_requires_segment_info', None)) or
				arg == 'pl'):
				continue
			if argspec.defaults and len(argspec.defaults) >= i:
				default = argspec.defaults[-i]
				defaults.append(default)
				args.append(arg)
			else:
				args.insert(0, arg)
		argspec = ArgSpec(args=args, varargs=argspec.varargs, keywords=argspec.keywords, defaults=tuple(defaults))

	return argspec
