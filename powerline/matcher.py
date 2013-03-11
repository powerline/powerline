# vim:fileencoding=utf-8:noet

from __future__ import absolute_import
import sys


def gen_matcher_getter(ext, import_paths):
	def get(match_name):
		match_module, separator, match_function = match_name.rpartition('.')
		if not separator:
			match_module = 'powerline.matchers.{0}'.format(ext)
			match_function = match_name
		oldpath = sys.path
		sys.path = import_paths + sys.path
		try:
			return getattr(__import__(match_module, fromlist=[match_function]), match_function)
		finally:
			sys.path = oldpath
	return get
