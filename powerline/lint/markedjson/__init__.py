# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lint.markedjson.loader import Loader


def load(stream, Loader=Loader):
	'''Parse JSON value and produce the corresponding Python object

	:return:
		(hadproblem, object) where first argument is true if there were errors 
		during loading JSON stream and second is the corresponding JSON object.
	'''
	loader = Loader(stream)
	try:
		r = loader.get_single_data()
		return r, loader.haserrors
	finally:
		loader.dispose()
