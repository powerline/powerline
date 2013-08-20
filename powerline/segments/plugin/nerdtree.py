# vim:fileencoding=utf-8:noet

import vim

from powerline.bindings.vim import getbufvar
from powerline.segments.vim import window_cached


@window_cached
def nerdtree(pl):
	ntr = getbufvar('%', 'NERDTreeRoot')
	if not ntr:
		return
	path_str = vim.eval('getbufvar("%", "NERDTreeRoot").path.str()')
	return [{
		'contents': path_str,
		'highlight_group': ['nerdtree.path', 'file_name'],
	}]
