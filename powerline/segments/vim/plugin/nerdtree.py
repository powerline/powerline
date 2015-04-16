# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.editors import with_input
from powerline.editors.vim import VimBufferVar


@with_input(('nerd_tree_root', VimBufferVar('NERDTreeRoot'), 'str'))
def nerdtree(pl, segment_info):
	'''Return directory that is shown by the current buffer.

	Highlight groups used: ``nerdtree:path`` or ``file_name``.
	'''
	if not segment_info['input']['nerd_tree_root']:
		return None
	return [{
		'contents': segment_info['input']['nerd_tree_root'],
		'highlight_groups': ['nerdtree:path', 'file_name'],
	}]
