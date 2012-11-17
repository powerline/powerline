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
			return vim.bindeval('function("'+f+'")')
		except vim.error:
			return None

	vim_globals = vim.bindeval('g:')

	def set_global_var(var, val):
		vim_globals[var] = val
else:
	import json
	class VimFunc(object):
		__slots__ = ('f','rettype')
		def __init__(self, f, rettype=None):
			self.f       = f
			self.rettype = rettype

		def __call__(self, *args):
			r = vim.eval(self.f+'('+json.dumps(args)[1:-1]+')')
			if self.rettype:
				return self.rettype(r)
			return r

	def get_vim_func(f):
		return VimFunc(f)

	def set_global_var(var, val):
		vim.command('let g:{0}={1}'.format(var, json.dumps(val)))

vim_funcs = {
		'winwidth' : get_vim_func('winwidth', rettype=int),
		'mode'     : get_vim_func('mode'),
		'fghead'   : get_vim_func('fugitive#head'),
		'line'     : get_vim_func('line', rettype=int),
		'col'      : get_vim_func('col', rettype=int),
		'expand'   : get_vim_func('expand'),
		'tbcurtag' : get_vim_func('tagbar#currenttag'),
		'sstlflag' : get_vim_func('SyntasticStatuslineFlag'),
		'hlexists' : get_vim_func('hlexists', rettype=int),
}

def statusline():
	winwidth = vim_funcs['winwidth'](0)

	# Prepare segment contents
	mode = modes[vim_funcs['mode']()]

	try:
		branch = vim_funcs['fghead'](5)
	except vim.error:
		vim_funcs['fghead'] = None
		branch = ''
	except TypeError:
		branch = ''
	if branch:
		branch = '⭠ ' + branch

	line_current = vim_funcs['line']('.')
	line_end     = vim_funcs['line']('$')
	line_percent = line_current * 100 // line_end

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

	# The Syntastic segment is center aligned (filler segment on each side) to show off how the filler segments work
	# Not necessarily how it's going to look in the final theme
	set_global_var('syntastic_stl_format', '⮃ %E{ ERRORS (%e) ⭡ %fe }%W{ WARNINGS (%w) ⭡ %fw } ⮁')
	try:
		syntastic = vim_funcs['sstlflag']()
	except vim.error:
		vim_funcs['sstlflag'] = None
		syntastic = ''
	except TypeError:
		syntastic = ''

	powerline = Powerline([
		Segment(mode, 22, 148, attr=Segment.ATTR_BOLD),
		Segment(vim.eval('&paste ? "PASTE" : ""'), 231, 166, attr=Segment.ATTR_BOLD),
		Segment(branch, 250, 240, priority=10),
		Segment(readonly, 196, 240, draw_divider=False),
		Segment(filepath, 250, 240, draw_divider=False, priority=5),
		Segment(filename, filename_color, 240, attr=Segment.ATTR_BOLD, draw_divider=not len(modified)),
		Segment(modified, 220, 240, attr=Segment.ATTR_BOLD),
		Segment(currenttag, 246, 236, draw_divider=False, priority=100),
		Segment(filler=True, fg=236, bg=236),
		Segment(syntastic, 214, 236, attr=Segment.ATTR_BOLD, draw_divider=False, priority=100),
		Segment(filler=True, fg=236, bg=236),
		Segment(vim.eval('&ff'), 247, 236, side='r', priority=50),
		Segment(vim.eval('&fenc'), 247, 236, side='r', priority=50),
		Segment(vim.eval('&ft'), 247, 236, side='r', priority=50),
		Segment(str(line_percent).rjust(3) + '%', line_percent_color, 240, side='r', priority=30),
		Segment('⭡ ', 239, 252, side='r'),
		Segment(str(line_current).rjust(3), 235, 252, attr=Segment.ATTR_BOLD, side='r', draw_divider=False),
		Segment(':' + str(col_current).ljust(2), 244, 252, side='r', priority=30, draw_divider=False),
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

statusline()

# vim: ft=python ts=4 sts=4 sw=4 noet
