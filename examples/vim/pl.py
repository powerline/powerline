# -*- coding: utf-8 -*-

from powerline.core import Powerline
from powerline.ext.vim.bindings import vim_get_func

vim_winwidth = vim_get_func('winwidth', rettype=int)
vim_getwinvar = vim_get_func('getwinvar')
vim_setwinvar = vim_get_func('setwinvar')

pl = Powerline('vim')


def statusline(winnr):
	current = vim_getwinvar(winnr, 'current')
	winwidth = vim_winwidth(winnr)

	mode = vim_get_func('mode')()
	if not current:
		mode = 'nc'

	statusline = pl.renderer.render(mode, winwidth)

	return statusline
