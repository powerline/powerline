# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_command_exists, vim_get_autoload_func
from powerline.theme import requires_segment_info


currenttag = None
tag_cache = {}


@requires_segment_info
def current_tag(segment_info, pl, flags='s'):
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
	global tag_cache
	window_id = segment_info['window_id']
	if segment_info['mode'] == 'nc':
		return tag_cache.get(window_id, (None,))[-1]
	if not currenttag:
		if vim_command_exists('Tagbar'):
			currenttag = vim_get_autoload_func('tagbar#currenttag')
			if not currenttag:
				return None
		else:
			return None
	prev_key, r = tag_cache.get(window_id, (None, None))
	key = (int(vim.eval('b:changedtick')), segment_info['window'].cursor[0])
	if prev_key and key == prev_key:
		return r
	r = currenttag('%s', '', flags)
	tag_cache[window_id] = (key, r)
	return r
