# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_getvar


initialized = False


def initialize(pl, shutdown_event):
	global initialized
	if initialized:
		return
	initialized = True
	vim.command(
		'''
		function! Ctrlp_status_main(focus, byfname, regex, prev, item, next, marked)
			let g:_powerline_ctrlp_status = {\
				'focus': a:focus,\
				'byfname': a:byfname,\
				'regex': a:regex,\
				'prev': a:prev,\
				'item': a:item,\
				'next': a:next,\
				'marked': a:marked,\
			}
			return ''
		endfunction

		function! Ctrlp_status_prog(str)
			let g:_powerline_ctrlp_status.prog = a:str
			return ''
		endfunction

		let g:ctrlp_status_func = {\
			'main': 'Ctrlp_status_main',\
			'prog': 'Ctrlp_status_prog',\
		}

		call ctrlp#call('s:opts')
		call ctrlp#statusline()
		'''
	)


def marked(pl):
	'''Returns boolean indicating whether anything is marked or not.

	Highlight groups used: ``ctrlp:marked``.
	'''
	status = vim_getvar('_powerline_ctrlp_status')
	if 'prog' in status or 'marked' not in status or status['marked'] == ' <->':
		return None
	return [{
		'highlight_groups': ['ctrlp:marked'],
		'contents': status['marked'].strip()
	}]
marked.startup = initialize


def mode(pl):
	'''Returns current mode.

	Highlight groups used: ``ctrlp:status``.
	'''
	status = vim_getvar('_powerline_ctrlp_status')
	if 'prog' in status or 'item' not in status:
		return None
	return [{
		'highlight_groups': ['ctrlp:status'],
		'contents': ' ' + status['item'] + ' '
	}]
mode.startup = initialize


def mode_prev(pl):
	'''Returns previous mode.

	Highlight groups used: ``ctrlp:status_other``.
	'''
	status = vim_getvar('_powerline_ctrlp_status')
	if 'prog' in status or 'prev' not in status:
		return None
	return [{
		'highlight_groups': ['ctrlp:status_other'],
		'contents': status['prev'] + ' '
	}]
mode_prev.startup = initialize


def mode_next(pl):
	'''Returns next mode.

	Highlight groups used: ``ctrlp:status_other``.
	'''
	status = vim_getvar('_powerline_ctrlp_status')
	if 'prog' in status or 'next' not in status:
		return None
	return [{
		'highlight_groups': ['ctrlp:status_other'],
		'contents': ' ' + status['next'] + ' '
	}]
mode_next.startup = initialize


def prog(pl):
	'''Returns progress status.

	Highlight groups used: ``ctrlp:prog``.
	'''
	status = vim_getvar('_powerline_ctrlp_status')
	if 'prog' not in status:
		return None
	return [{
		'highlight_groups': ['ctrlp:prog'],
		'contents': status['prog']
	}]
prog.startup = initialize
