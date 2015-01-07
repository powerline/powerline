# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from functools import wraps


def wraps_saveargs(wrapped):
	def dec(wrapper):
		r = wraps(wrapped)(wrapper)
		r.powerline_origin = getattr(wrapped, 'powerline_origin', wrapped)
		return r
	return dec


def add_divider_highlight_group(highlight_group):
	def dec(func):
		@wraps_saveargs(func)
		def f(**kwargs):
			r = func(**kwargs)
			if r:
				return [{
					'contents': r,
					'divider_highlight_group': highlight_group,
				}]
			else:
				return None
		return f
	return dec
