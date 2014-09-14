# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.bindings.vim import buffer_name


try:
	import vim
except ImportError:
	pass
else:
	vim.command('''
	function! Powerline_plugin_ctrlp_main(...)
		let b:powerline_ctrlp_type = 'main'
		let b:powerline_ctrlp_args = a:000
	endfunction''')

	vim.command('''
	function! Powerline_plugin_ctrlp_prog(...)
		let b:powerline_ctrlp_type = 'prog'
		let b:powerline_ctrlp_args = a:000
	endfunction''')

	vim.command('''
		let g:ctrlp_status_func = {'main': 'Powerline_plugin_ctrlp_main', 'prog': 'Powerline_plugin_ctrlp_prog'}
	''')


def ctrlp(matcher_info):
	name = buffer_name(matcher_info)
	return name and os.path.basename(name) == b'ControlP'
