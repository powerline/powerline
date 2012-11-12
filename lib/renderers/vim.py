#!/usr/bin/env python

from lib.core import Segment
from lib.renderers import SegmentRenderer


class VimSegmentRenderer(SegmentRenderer):
	'''Powerline vim segment renderer.
	'''
	def __init__(self):
		self.hl_groups = {}

	def hl(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it's added to the vim highlight group.
		'''
		hl_group = {
			'ctermfg': 'NONE',
			'guifg': 'NONE',
			'ctermbg': 'NONE',
			'guibg': 'NONE',
			'attr': ['NONE'],
		}

		# We don't need to explicitly reset attributes in vim, so skip those calls
		if not attr and not bg and not fg:
			return ''

		if fg is not None and fg is not False:
			hl_group['ctermfg'] = fg[0]
			hl_group['guifg'] = fg[1]

		if bg is not None and bg is not False:
			hl_group['ctermbg'] = bg[0]
			hl_group['guibg'] = bg[1]

		if attr is not None and attr is not False and attr != 0:
			hl_group['attr'] = []
			if attr & Segment.ATTR_BOLD:
				hl_group['attr'].append('bold')
			if attr & Segment.ATTR_ITALIC:
				hl_group['attr'].append('italic')
			if attr & Segment.ATTR_UNDERLINE:
				hl_group['attr'].append('underline')

		hl_group_name = 'Pl_{ctermfg}_{guifg}_{ctermbg}_{guibg}_{attr}'.format(
			ctermfg=hl_group['ctermfg'],
			guifg=hl_group['guifg'],
			ctermbg=hl_group['ctermbg'],
			guibg=hl_group['guibg'],
			attr=''.join(attr[0] for attr in hl_group['attr']),
		)

		self.hl_groups[hl_group_name] = hl_group

		return '%#{0}#'.format(hl_group_name)

	def get_hl_statements(self):
		'''Return vimscript highlight statements.

		Returns a string with all the required highlight statements for vim.
		Requires the statusline to be rendered using the Segment.render()
		method first as this method generates all the necessary highlighting
		information.
		'''
		return '\n'.join(['hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
				group=group,
				ctermfg=hl['ctermfg'],
				guifg='#{0:06x}'.format(hl['guifg']) if hl['guifg'] != 'NONE' else 'NONE',
				ctermbg=hl['ctermbg'],
				guibg='#{0:06x}'.format(hl['guibg']) if hl['guibg'] != 'NONE' else 'NONE',
				attr=','.join(hl['attr']),
			) for group, hl in self.hl_groups.items()])
