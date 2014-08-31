# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lint.markedjson.loader import Loader


def load(stream, Loader=Loader):
	"""
	Parse the first YAML document in a stream
	and produce the corresponding Python object.
	"""
	loader = Loader(stream)
	try:
		r = loader.get_single_data()
		return r, loader.haserrors
	finally:
		loader.dispose()
