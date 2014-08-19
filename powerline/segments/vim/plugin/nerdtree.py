# vim:fileencoding=utf-8:noet

try:
	import vim
except ImportError:
	vim = object()  # NOQA

from powerline.bindings.vim import bufvar_exists
from powerline.segments.vim import window_cached


@window_cached
def nerdtree(pl):
	'''Return directory that is shown by the current buffer.

	Highlight groups used: ``nerdtree.path`` or ``file_name``.
	'''
	if not bufvar_exists(None, 'NERDTreeRoot'):
		return None
	path_str = vim.eval('getbufvar("%", "NERDTreeRoot").path.str()')
	return [{
		'contents': path_str,
		'highlight_group': ['nerdtree.path', 'file_name'],
	}]
