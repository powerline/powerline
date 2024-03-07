# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_func_exists
from powerline.theme import requires_segment_info


@requires_segment_info
def obsession_indicator(pl, segment_info, text='rec.'):
	'''Shows the indicator if tpope/vim-obsession plugin is enabled

	:param str text:
		String to show when obsession is recording sessions.
	'''
	if not vim_func_exists('ObsessionStatus'):
		return None
	return text if vim.eval('ObsessionStatus("on","off")') == "on"  else None
