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
		Specifies additional properties of the displayed tag.  
		Supported values:

		* s - display complete signature
		* f - display the full hierarchy of the tag
		* p - display the raw prototype

		More info at `official doc
		<https://github.com/majutsushi/tagbar/blob/master/doc/tagbar.txt>`_
		(search for 'tagbar#currenttag').
	'''
	if not int(vim.eval('exists(":Tagbar")')):
		return
	return vim.eval('tagbar#currenttag("%s", "", "{0}")'.format(flags))
