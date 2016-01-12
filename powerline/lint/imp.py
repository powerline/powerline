# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.lint.selfcheck import havemarks


class WithPath(object):
	def __init__(self, import_paths):
		self.import_paths = import_paths

	def __enter__(self):
		self.oldpath = sys.path
		sys.path = self.import_paths + sys.path

	def __exit__(self, *args):
		sys.path = self.oldpath


def import_function(function_type, name, data, context, echoerr, module):
	havemarks(name, module)

	if module == 'powerline.segments.i3wm' and name == 'workspaces':
		echoerr(context='Warning while checking segments (key {key})'.format(key=context.key),
		        context_mark=name.mark,
		        problem='segment {0} from {1} is deprecated'.format(name, module),
		        problem_mark=module.mark)

	with WithPath(data['import_paths']):
		try:
			func = getattr(__import__(str(module), fromlist=[str(name)]), str(name))
		except ImportError:
			echoerr(context='Error while checking segments (key {key})'.format(key=context.key),
			        context_mark=name.mark,
			        problem='failed to import module {0}'.format(module),
			        problem_mark=module.mark)
			return None
		except AttributeError:
			echoerr(context='Error while loading {0} function (key {key})'.format(function_type, key=context.key),
			        problem='failed to load function {0} from module {1}'.format(name, module),
			        problem_mark=name.mark)
			return None

	if not callable(func):
		echoerr(context='Error while checking segments (key {key})'.format(key=context.key),
		        context_mark=name.mark,
		        problem='imported “function” {0} from module {1} is not callable'.format(name, module),
		        problem_mark=module.mark)
		return None

	return func


def import_segment(*args, **kwargs):
	return import_function('segment', *args, **kwargs)
