# -*- coding: utf-8 -*-

import vim
from powerline.core import Powerline
from powerline.ext.vim.bindings import vim_get_func

vim_winwidth = vim_get_func('winwidth', rettype=int)
vim_hlexists = vim_get_func('hlexists', rettype=int)
vim_getwinvar = vim_get_func('getwinvar')
vim_setwinvar = vim_get_func('setwinvar')

created_hl_groups = []
percent_placeholder = u''

pl = Powerline('vim')


def statusline(winnr):
	current = vim_getwinvar(winnr, 'current')
	windata = vim_getwinvar(winnr, 'powerline')
	winwidth = vim_winwidth(winnr)

	if current or not windata:
		mode = vim_get_func('mode')()
		if mode == 'n':
			mode = '__default__'

		stl = pl.render(mode, winwidth)

		vim_setwinvar(winnr, 'powerline', stl)
	else:
		mode = 'nc'
		stl = vim_getwinvar(winnr, 'powerline').decode('utf-8')

	# Replace percent placeholders
	stl = stl.replace(percent_placeholder, '%%')

	# Create highlighting groups
	for hl in pl.renderer.hl_groups.values():
		if hl['name'] in created_hl_groups:
			continue

		vim.command('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
				group=hl['name'],
				ctermfg=hl['ctermfg'],
				guifg='#{0:06x}'.format(hl['guifg']) if hl['guifg'] != 'NONE' else 'NONE',
				ctermbg=hl['ctermbg'],
				guibg='#{0:06x}'.format(hl['guibg']) if hl['guibg'] != 'NONE' else 'NONE',
				attr=','.join(hl['attr']),
			))

		created_hl_groups.append(hl['name'])

	return stl
