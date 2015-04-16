# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.editors import with_input


@with_input('tab_amount')
def single_tab(pl, segment_info, mode):
	'''Returns True if Vim has only one tab opened
	'''
	return segment_info['input']['tab_amount'] == 1
