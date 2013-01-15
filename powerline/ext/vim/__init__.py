# -*- coding: utf-8 -*-


def source_plugin():
	import os
	import vim
	from bindings import vim_get_func
	fnameescape = vim_get_func('fnameescape')
	vim.command('source ' + fnameescape(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'powerline.vim')))
