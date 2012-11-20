# -*- coding: utf-8 -*-

import vim
import os
import re

from lib.core import Powerline, Segment
from lib.renderers import VimSegmentRenderer

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

if hasattr(vim, 'bindeval'):
	# This branch is used to avoid invoking vim parser as much as possible

	def get_vim_func(f, rettype=None):
		try:
			return vim.bindeval('function("' + f + '")')
		except vim.error:
			return None

	vim_globals = vim.bindeval('g:')

	def set_global_var(var, val):
		vim_globals[var] = val
else:
	import json

	class VimFunc(object):
		__slots__ = ('f', 'rettype')

		def __init__(self, f, rettype=None):
			self.f = f
			self.rettype = rettype

		def __call__(self, *args):
			r = vim.eval(self.f + '(' + json.dumps(args)[1:-1] + ')')
			if self.rettype:
				return self.rettype(r)
			return r

	get_vim_func = VimFunc

	def set_global_var(var, val):  # NOQA
		vim.command('let g:{0}={1}'.format(var, json.dumps(val)))

vim_funcs = {
	'winwidth': get_vim_func('winwidth', rettype=int),
	'mode': get_vim_func('mode'),
	'fghead': get_vim_func('fugitive#head'),
	'line': get_vim_func('line', rettype=int),
	'col': get_vim_func('col', rettype=int),
	'expand': get_vim_func('expand'),
	'tbcurtag': get_vim_func('tagbar#currenttag'),
	'hlexists': get_vim_func('hlexists', rettype=int),
}

getwinvar = get_vim_func('getwinvar')
setwinvar = get_vim_func('setwinvar')


def statusline(winnr):
	winwidth = vim_funcs['winwidth'](winnr)

	current = getwinvar(winnr, 'current')
	windata = getwinvar(winnr, 'powerline')

	if current:
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
			branch = '⭠ ' + branch

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
			'paste': vim.eval('&paste ? "PASTE" : ""'),
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
			'line_percent': str(line_percent).rjust(3) + '%',
			'line_percent_color': line_percent_color,
			'linecurrent': str(line_current).rjust(3),
			'colcurrent': ':' + str(col_current).ljust(2),
		}

		setwinvar(winnr, 'powerline', windata)

	mode = modes[vim_funcs['mode']()]

	if not current:
		mode = None

	powerline = Powerline([
		Segment(mode, 22, 148, attr=Segment.ATTR_BOLD),
		Segment(windata['paste'], 231, 166, attr=Segment.ATTR_BOLD),
		Segment(windata['branch'], 250, 240, priority=10),
		Segment(windata['readonly'], 196, 240, draw_divider=False),
		Segment(windata['filepath'], 250, 240, draw_divider=False, priority=5),
		Segment(windata['filename'], windata['filename_color'], 240, attr=Segment.ATTR_BOLD, draw_divider=not len(windata['modified'])),
		Segment(windata['modified'], 220, 240, attr=Segment.ATTR_BOLD),
		Segment(windata['currenttag'], 246, 236, draw_divider=False, priority=100),
		Segment(filler=True, fg=236, bg=236),
		Segment(windata['fileformat'], 247, 236, side='r', priority=50),
		Segment(windata['fileencoding'], 247, 236, side='r', priority=50),
		Segment(windata['filetype'], 247, 236, side='r', priority=50),
		Segment(windata['line_percent'], windata['line_percent_color'], 240, side='r', priority=30),
		Segment('⭡ ', 239, 252, side='r'),
		Segment(windata['linecurrent'], 235, 252, attr=Segment.ATTR_BOLD, side='r', draw_divider=False),
		Segment(windata['colcurrent'], 244, 252, side='r', priority=30, draw_divider=False),
	])

	renderer = VimSegmentRenderer()
	stl = powerline.render(renderer, winwidth)

	# Escape percent chars in the statusline, but only if they aren't part of any stl escape sequence
	stl = re.sub('(\w+)\%(?![-{()<=#*%])', '\\1%%', stl)

	# Create highlighting groups
	for group, hl in renderer.hl_groups.items():
		if vim_funcs['hlexists'](group):
			# Only create hl group if it doesn't already exist
			continue

		vim.command('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
				group=group,
				ctermfg=hl['ctermfg'],
				guifg='#{0:06x}'.format(hl['guifg']) if hl['guifg'] != 'NONE' else 'NONE',
				ctermbg=hl['ctermbg'],
				guibg='#{0:06x}'.format(hl['guibg']) if hl['guibg'] != 'NONE' else 'NONE',
				attr=','.join(hl['attr']),
			))

	return stl

# vim: ft=python ts=4 sts=4 sw=4 noet
