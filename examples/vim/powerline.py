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


def statusline():
	winwidth = int(vim.bindeval('winwidth(0)'))

	# Prepare segment contents
	mode = modes[vim.bindeval('mode()')]

	branch = vim.bindeval('fugitive#head(5)')
	if branch:
		branch = '⭠ ' + branch

	line_current = int(vim.bindeval('line(".")'))
	line_end = int(vim.bindeval('line("$")'))
	line_percent = int(float(line_current) / float(line_end) * 100)

	# Fun gradient colored percent segment
	line_percent_gradient = [160, 166, 172, 178, 184, 190]
	line_percent_color = line_percent_gradient[int((len(line_percent_gradient) - 1) * line_percent / 100)]

	col_current = vim.bindeval('col(".")')

	filepath = os.path.split(vim.bindeval('expand("%:~:.")'))
	filename_color = 231
	if filepath[0]:
		filepath[0] += os.sep

	if not filepath[1]:
		filepath = ('', '[No Name]')
		filename_color = 250

	readonly = vim.bindeval('&ro ? "⭤ " : ""')
	modified = vim.bindeval('&mod ? " +" : ""')

	currenttag = vim.bindeval('tagbar#currenttag("%s", "")')

	# The Syntastic segment is center aligned (filler segment on each side) to show off how the filler segments work
	# Not necessarily how it's going to look in the final theme
	vim.command('let g:syntastic_stl_format = "⮃ %E{ ERRORS (%e) ⭡ %fe }%W{ WARNINGS (%w) ⭡ %fw } ⮁"')
	syntastic = vim.bindeval('SyntasticStatuslineFlag()')

	powerline = Powerline([
		Segment(mode, 22, 148, attr=Segment.ATTR_BOLD),
		Segment(vim.bindeval('&paste ? "PASTE" : ""'), 231, 166, attr=Segment.ATTR_BOLD),
		Segment(branch, 250, 240, priority=10),
		Segment(readonly, 196, 240, draw_divider=False),
		Segment(filepath[0], 250, 240, draw_divider=False, priority=5),
		Segment(filepath[1], filename_color, 240, attr=Segment.ATTR_BOLD, draw_divider=not len(modified)),
		Segment(modified, 220, 240, attr=Segment.ATTR_BOLD),
		Segment(currenttag, 246, 236, draw_divider=False, priority=100),
		Segment(filler=True, fg=236, bg=236),
		Segment(syntastic, 214, 236, attr=Segment.ATTR_BOLD, draw_divider=False, priority=100),
		Segment(filler=True, fg=236, bg=236),
		Segment(vim.bindeval('&ff'), 247, 236, side='r', priority=50),
		Segment(vim.bindeval('&fenc'), 247, 236, side='r', priority=50),
		Segment(vim.bindeval('&ft'), 247, 236, side='r', priority=50),
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
		if int(vim.bindeval('hlexists("{0}")'.format(group))):
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
