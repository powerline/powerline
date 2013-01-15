# -*- coding: utf-8 -*-

from powerline.ext.vim.bindings import vim_get_func
from powerline.renderer import Renderer

import vim

vim_mode = vim_get_func('mode')
vim_winwidth = vim_get_func('winwidth', rettype=int)
vim_getwinvar = vim_get_func('getwinvar')
vim_setwinvar = vim_get_func('setwinvar')


class VimRenderer(Renderer):
	'''Powerline vim segment renderer.'''
	PERCENT_PLACEHOLDER = u''

	def __init__(self, *args, **kwargs):
		super(VimRenderer, self).__init__(*args, **kwargs)
		self.hl_groups = {}
		self.window_cache = {}

	def render(self, winnr, current):
		'''Render all segments.

		This method handles replacing of the percent placeholder for vim
		statuslines, and it caches segment contents which are retrieved and
		used in non-current windows.
		'''
		window_id = vim_getwinvar(winnr, 'window_id')
		winwidth = vim_winwidth(winnr)
		if current:
			mode = vim_mode()
			theme = self.get_theme()
			segments = [segment for segment in theme.get_segments()]
			self.window_cache[window_id] = (theme, segments)
		else:
			mode = 'nc'
			theme, segments = self.window_cache.get(window_id, (None, None))
		statusline = super(VimRenderer, self).render(mode, winwidth, theme, segments)
		statusline = statusline.replace(self.PERCENT_PLACEHOLDER, '%%')
		return statusline

	def hl(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it's added to the vim highlight group.
		'''
		# We don't need to explicitly reset attributes in vim, so skip those calls
		if not attr and not bg and not fg:
			return ''

		if not (fg, bg, attr) in self.hl_groups:
			hl_group = {
				'ctermfg': 'NONE',
				'guifg': 'NONE',
				'ctermbg': 'NONE',
				'guibg': 'NONE',
				'attr': ['NONE'],
				'name': '',
				}
			if fg is not None and fg is not False:
				hl_group['ctermfg'] = fg[0]
				hl_group['guifg'] = fg[1]
			if bg is not None and bg is not False:
				hl_group['ctermbg'] = bg[0]
				hl_group['guibg'] = bg[1]
			if attr:
				hl_group['attr'] = []
				if attr & self.ATTR_BOLD:
					hl_group['attr'].append('bold')
				if attr & self.ATTR_ITALIC:
					hl_group['attr'].append('italic')
				if attr & self.ATTR_UNDERLINE:
					hl_group['attr'].append('underline')
			hl_group['name'] = 'Pl_' + \
				str(hl_group['ctermfg']) + '_' + \
				str(hl_group['guifg']) + '_' + \
				str(hl_group['ctermbg']) + '_' + \
				str(hl_group['guibg']) + '_' + \
				''.join(hl_group['attr'])
			self.hl_groups[(fg, bg, attr)] = hl_group
			vim.command('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
					group=hl_group['name'],
					ctermfg=hl_group['ctermfg'],
					guifg='#{0:06x}'.format(hl_group['guifg']) if hl_group['guifg'] != 'NONE' else 'NONE',
					ctermbg=hl_group['ctermbg'],
					guibg='#{0:06x}'.format(hl_group['guibg']) if hl_group['guibg'] != 'NONE' else 'NONE',
					attr=','.join(hl_group['attr']),
				))
		return '%#' + self.hl_groups[(fg, bg, attr)]['name'] + '#'
