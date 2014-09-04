# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.bindings.vim import list_tabpages


def single_tab(pl, segment_info, mode):
	'''Returns True if Vim has only one tab opened
	'''
	return len(list_tabpages()) == 1
