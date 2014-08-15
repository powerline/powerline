# vim:fileencoding=utf-8:noet

try:
	import vim
except ImportError:
	vim = object()  # NOQA

from powerline.segments.vim import window_cached


@window_cached
def current_tag(pl):
	if not int(vim.eval('exists(":Tagbar")')):
		return
	return vim.eval('tagbar#currenttag("%s", "")')
