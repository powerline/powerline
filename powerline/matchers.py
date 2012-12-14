# -*- coding: utf-8 -*-

from importlib import import_module
import sys

class Matchers(object):
	def __init__(self, ext, path):
		self.ext = ext
		self.path = path

	def get(self, match_name):
		match_module, separator, match_function = match_name.rpartition('.')
		if not separator:
			match_module = 'powerline.ext.{0}.matchers'.format(self.ext)
			match_function = match_name

		oldpath = sys.path
		sys.path = self.path + sys.path

		try:
			return getattr(import_module(match_module), match_function)
		finally:
			sys.path = oldpath

# vim: noet tw=120
