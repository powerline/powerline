# -*- coding: utf-8 -*-

from importlib import import_module
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
			return getattr(import_module(match_module), match_function)
		finally:
			sys.path = oldpath
	return get
