# -*- coding: utf-8 -*-

import vim
import os

from powerline.core import Powerline
from powerline.segment import mksegment
from powerline.ext.vim import VimRenderer
from powerline.ext.vim.bindings import vim_get_func

modes = {
	'n': 'NORMAL',
	'no': 'N·OPER',
	'v': 'VISUAL',
	'V': 'V·LINE',
	'': 'V·BLCK',
	's': 'SELECT',
	'S': 'S·LINE',
	'': 'S·BLCK',
	'i': 'INSERT',
	'R': 'REPLACE',
	'Rv': 'V·RPLCE',
	'c': 'COMMND',
	'cv': 'VIM EX',
	'ce': 'EX',
	'r': 'PROMPT',
	'rm': 'MORE',
	'r?': 'CONFIRM',
	'!': 'SHELL',
}

# We need to replace this private use glyph with a double-percent later
percent_placeholder = u''

vim_funcs = {
	'winwidth': vim_get_func('winwidth', rettype=int),
	'mode': vim_get_func('mode'),
	'fghead': vim_get_func('fugitive#head'),
	'line': vim_get_func('line', rettype=int),
	'col': vim_get_func('col', rettype=int),
	'expand': vim_get_func('expand'),
	'tbcurtag': vim_get_func('tagbar#currenttag'),
	'hlexists': vim_get_func('hlexists', rettype=int),
}

getwinvar = vim_get_func('getwinvar')
setwinvar = vim_get_func('setwinvar')


def statusline(winnr):
	winwidth = vim_funcs['winwidth'](winnr)

	current = getwinvar(winnr, 'current')
	windata = getwinvar(winnr, 'powerline')

	if current or not windata.keys():
		# Recreate segment data for each redraw if we're in the current window
		line_current = vim_funcs['line']('.')
		line_end = vim_funcs['line']('$')
		line_percent = line_current * 100 // line_end

		try:
			branch = vim_funcs['fghead'](5)
		except vim.error:
			vim_funcs['fghead'] = None
			branch = ''
		except TypeError:
			branch = ''
		if branch:
			branch = u'⭠ ' + branch

		# Fun gradient colored percent segment
		line_percent_gradient = [160, 166, 172, 178, 184, 190]
		line_percent_color = line_percent_gradient[int((len(line_percent_gradient) - 1) * line_percent / 100)]

		col_current = vim_funcs['col']('.')

		filepath, filename = os.path.split(vim_funcs['expand']('%:~:.'))
		filename_color = 231
		if filepath:
			filepath += os.sep

		if not filename:
			filename = '[No Name]'
			filename_color = 250

		readonly = vim.eval('&ro ? "⭤ " : ""')
		modified = vim.eval('&mod ? " +" : ""')

		try:
			currenttag = vim_funcs['tbcurtag']('%s', '')
		except vim.error:
			vim_funcs['tbcurtag'] = None
			currenttag = ''
		except TypeError:
			currenttag = ''

		windata = {
			'paste': vim.eval('&paste ? "PASTE" : ""') or None,
			'branch': branch,
			'readonly': readonly,
			'filepath': filepath,
			'filename': filename,
			'filename_color': filename_color,
			'modified': modified,
			'currenttag': currenttag,
			'fileformat': vim.eval('&ff'),
			'fileencoding': vim.eval('&fenc'),
			'filetype': vim.eval('&ft'),
			'line_percent': str(line_percent).rjust(3) + percent_placeholder,
			'line_percent_color': line_percent_color,
			'linecurrent': str(line_current).rjust(3),
			'colcurrent': ':' + str(col_current).ljust(2),
		}

		# Horrible workaround for missing None type for vimdicts
		windata = {k: v if v is not None else '__None__' for k, v in windata.items()}

		setwinvar(winnr, 'powerline', windata)

	mode = modes[vim_funcs['mode']()]

	if not current:
		mode = None

	# Horrible workaround for missing None type for vimdicts
	windata = {k: windata[k] if windata[k] != '__None__' else None for k in windata.keys()}

	powerline = Powerline([
		mksegment(mode, 22, 148, attr=VimRenderer.ATTR_BOLD),
		mksegment(windata['paste'], 231, 166, attr=VimRenderer.ATTR_BOLD),
		mksegment(windata['branch'], 250, 240, priority=60),
		mksegment(windata['readonly'], 196, 240, draw_divider=False),
		mksegment(windata['filepath'], 250, 240, draw_divider=False, priority=40),
		mksegment(windata['filename'], windata['filename_color'], 240, attr=VimRenderer.ATTR_BOLD, draw_divider=False),
		mksegment(windata['modified'], 220, 240, attr=VimRenderer.ATTR_BOLD),
		mksegment(windata['currenttag'], 246, 236, draw_divider=False, priority=100),
		mksegment(filler=True, cterm_fg=236, cterm_bg=236),
		mksegment(windata['fileformat'], 247, 236, side='r', priority=50, draw_divider=False),
		mksegment(windata['fileencoding'], 247, 236, side='r', priority=50),
		mksegment(windata['filetype'], 247, 236, side='r', priority=50),
		mksegment(windata['line_percent'], windata['line_percent_color'], 240, side='r', priority=30),
		mksegment(u'⭡ ', 239, 252, side='r'),
		mksegment(windata['linecurrent'], 235, 252, attr=VimRenderer.ATTR_BOLD, side='r', draw_divider=False),
		mksegment(windata['colcurrent'], 244, 252, side='r', priority=30, draw_divider=False),
	])

	renderer = VimRenderer
	stl = powerline.render(renderer, winwidth)

	# Replace percent placeholders
	stl = stl.replace(percent_placeholder, '%%')

	# Create highlighting groups
	for idx, hl in powerline.renderer.hl_groups.items():
		if vim_funcs['hlexists'](hl['name']):
			# Only create hl group if it doesn't already exist
			continue

		vim.command('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
				group=hl['name'],
				ctermfg=hl['ctermfg'],
				guifg='#{0:06x}'.format(hl['guifg']) if hl['guifg'] != 'NONE' else 'NONE',
				ctermbg=hl['ctermbg'],
				guibg='#{0:06x}'.format(hl['guibg']) if hl['guibg'] != 'NONE' else 'NONE',
				attr=','.join(hl['attr']),
			))

	return stl

# vim: ft=python ts=4 sts=4 sw=4 noet
