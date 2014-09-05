# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.segments.vim import window_cached


@window_cached
def current_tag(pl):
	if not int(vim.eval('exists(":Tagbar")')):
		return
	return vim.eval('tagbar#currenttag("%s", "")')
