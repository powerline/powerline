# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import create_ruby_dpowerline


def initialize():
	global initialized
	if initialized:
		return
	initialized = True
	vim.command('echom 3210')
	vim.command('let g:ctrlp_status = {}')
	vim.command(
		'''
		execute 'function! Ctrlp_status_main(focus, byfname, regex, prev, item, next, marked)
			let g:ctrlp_status = {\
"focus": a:focus,\
"byfname": a:byfname,\
"regex": a:regex,\
"prev": a:prev,\
"item": a:item,\
"next": a:next,\
"marked": a:marked,\
}
			return ""
		endfunction'
		'''
	)
	vim.command(
		'''
		execute 'function! Ctrlp_status_prog(str)
			let g:ctrlp_status["prog"] = a:str
			return ""
		endfunction'
		'''
	)
	vim.command(
		'''
		let g:ctrlp_status_func = {\
			'main': 'Ctrlp_status_main',\
			'prog': 'Ctrlp_status_prog',\
		}
		'''
	)

initialized = False

def marked(pl):
	initialize()
	status = vim.eval('g:ctrlp_status')
	if 'prog' in status:
		return []
	return None if status['marked'] == ' <->' else [{
		'highlight_groups': ['ctrlp:marked'],
		'contents': status['marked'].strip()
	}]

def mode(pl):
	initialize()
	status = vim.eval('g:ctrlp_status')
	if 'prog' in status:
		return []
	return [{
		'highlight_groups': ['ctrlp:status'],
		'contents': ' ' + status['item'] + ' '
	}]

def mode_prev(pl):
	initialize()
	status = vim.eval('g:ctrlp_status')
	if 'prog' in status:
		return []
	return [{
		'highlight_groups': ['ctrlp:status_other'],
		'contents': status['prev'] + ' '
	}]

def mode_next(pl):
	initialize()
	status = vim.eval('g:ctrlp_status')
	if 'prog' in status:
		return []
	return [{
		'highlight_groups': ['ctrlp:status_other'],
		'contents': ' ' + status['next']
	}]

def prog(pl):
	initialize()
	status = vim.eval('g:ctrlp_status')
	if 'prog' not in status:
		return []
	return [{
		'highlight_groups': ['ctrlp:prog'],
		'contents': status['prog']
	}]
