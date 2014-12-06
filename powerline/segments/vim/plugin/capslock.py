# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_func_exists
from powerline.theme import requires_segment_info


@requires_segment_info
def capslock_indicator(pl, segment_info, text='CAPS'):
	'''Shows the indicator if tpope/vim-capslock plugin is enabled

	.. note::
		In the current state plugin automatically disables itself when leaving 
		insert mode. So trying to use this segment not in insert or replace 
		modes is useless.

	:param str text:
		String to show when software capslock presented by this plugin is 
		active.
	'''
	if not vim_func_exists('CapsLockStatusline'):
		return None
	# CapsLockStatusline() function returns an empty string when plugin is 
	# disabled. If it is not then string is non-empty.
	return text if vim.eval('CapsLockStatusline()') else None
