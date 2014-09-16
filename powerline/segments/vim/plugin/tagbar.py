# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.segments.vim import window_cached


@window_cached
def current_tag(pl, flags='s'):
	'''Return tag that is near the cursor.

	:param str flags:
		Specifies additional properties of the displayed tag. Supported values:

		* s - display complete signature
		* f - display the full hierarchy of the tag
		* p - display the raw prototype

		More info in the `official documentation`_ (search for 
		“tagbar#currenttag”).

		.. _`official documentation`: https://github.com/majutsushi/tagbar/blob/master/doc/tagbar.txt
	'''
	if not int(vim.eval('exists(":Tagbar")')):
		return None
	return vim.eval('tagbar#currenttag("%s", "", "{0}")'.format(flags))
