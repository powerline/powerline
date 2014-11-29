# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.segments.vim import window_cached
from powerline.bindings.vim import vim_command_exists, vim_get_autoload_func


currenttag = None


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
	global currenttag
	if not currenttag:
		if vim_command_exists('Tagbar'):
			currenttag = vim_get_autoload_func('tagbar#currenttag')
			if not currenttag:
				return None
		else:
			return None
	return currenttag('%s', '', flags)
