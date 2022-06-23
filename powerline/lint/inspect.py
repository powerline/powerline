# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from inspect import FullArgSpec, getfullargspec
from itertools import zip_longest

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
		argspec = getfullargspec(method)
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

	return FullArgSpec(args=args, varargs=None, varkw=None, defaults=tuple(defaults), kwonlyargs=(), kwonlydefaults={}, annotations={})


def formatconfigargspec(args, varargs=None, varkw=None, defaults=None,
                        kwonlyargs=(), kwonlydefaults={}, annotations={},
                        formatvalue=lambda value: '=' + repr(value)):
	'''Format an argument spec from the values returned by getconfigargspec.

	This is a specialized replacement for inspect.formatargspec, which has been
	deprecated since Python 3.5 and was removed in Python 3.11. It supports
	valid values for args, defaults and formatvalue; all other parameters are
	expected to be either empty or None.
	'''
	assert varargs is None
	assert varkw is None
	assert not kwonlyargs
	assert not kwonlydefaults
	assert not annotations

	specs = []
	if defaults:
		firstdefault = len(args) - len(defaults)
	for i, arg in enumerate(args):
		spec = arg
		if defaults and i >= firstdefault:
			spec += formatvalue(defaults[i - firstdefault])
		specs.append(spec)
	return '(' + ', '.join(specs) + ')'
