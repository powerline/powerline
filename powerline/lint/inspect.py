# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from inspect import ArgSpec, getargspec

from powerline.segments import Segment


def getconfigargspec(obj):
	if hasattr(obj, 'powerline_origin'):
		obj = obj.powerline_origin
	else:
		obj = obj

	args = []
	defaults = []

	if isinstance(obj, Segment):
		additional_args = obj.additional_args()
		argspecobjs = obj.argspecobjs()
		get_omitted_args = obj.omitted_args
	else:
		additional_args = ()
		argspecobjs = ((None, obj),)
		get_omitted_args = lambda *args: ()

	for arg in additional_args:
		args.append(arg[0])
		if len(arg) > 1:
			defaults.append(arg[1])

	requires_segment_info = hasattr(obj, 'powerline_requires_segment_info')
	requires_filesystem_watcher = hasattr(obj, 'powerline_requires_filesystem_watcher')

	for name, method in argspecobjs:
		argspec = getargspec(method)
		omitted_args = get_omitted_args(name, method)
		largs = len(argspec.args)
		for i, arg in enumerate(reversed(argspec.args)):
			if (
				largs - (i + 1) in omitted_args
				or arg in omitted_args
				or arg == 'pl'
				or arg == 'self'
				or (arg == 'create_watcher' and requires_filesystem_watcher)
				or (arg == 'segment_info' and requires_segment_info)
			):
				continue
			if argspec.defaults and len(argspec.defaults) > i:
				if arg in args:
					idx = args.index(arg)
					if len(args) - idx > len(defaults):
						args.pop(idx)
					else:
						continue
				default = argspec.defaults[-(i + 1)]
				defaults.append(default)
				args.append(arg)
			else:
				if arg not in args:
					args.insert(0, arg)

	return ArgSpec(args=args, varargs=None, keywords=None, defaults=tuple(defaults))
