# vim:fileencoding=utf-8:noet

try:
	import vim
except ImportError:
	vim = object()  # NOQA

from powerline.bindings.vim import getbufvar
from powerline.segments.vim import window_cached


@window_cached
def nerdtree(pl):
	'''Return directory that is shown by the current buffer.

	Highlight groups used: ``nerdtree.path`` or ``file_name``.
	'''
	ntr = getbufvar('%', 'NERDTreeRoot')
	if not ntr:
		return
	path_str = vim.eval('getbufvar("%", "NERDTreeRoot").path.str()')
	return [{
		'contents': path_str,
		'highlight_group': ['nerdtree.path', 'file_name'],
	}]
