# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.bindings.vim import VimEnviron, current_tabpage, get_vim_encoding
from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE
from powerline.lib.unicode import unichr, register_strwidth_error


mode_translations = {
	unichr(ord('V') - 0x40): '^V',
	unichr(ord('S') - 0x40): '^S',
}


class VimRenderer(Renderer):
	'''Powerline vim segment renderer.'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('%')] = '%%'

	def __init__(self, vim=None, is_old_vim=False, vim_funcs=None, vim_cls=None, **kwargs):
		self.vim = vim
		self.is_old_vim = is_old_vim
		if hasattr(self.vim, 'strwidth'):
			if sys.version_info < (3,):
				def strwidth(string):
					# Does not work with tabs, but neither is strwidth from default 
					# renderer
					return vim.strwidth(string.encode(self.encoding, 'replace'))
			else:
				def strwidth(string):
					return vim.strwidth(string)

			self.strwidth = strwidth
		else:
			# Hope nobody want to change this at runtime
			if self.vim.eval('&ambiwidth') == 'double':
				kwargs = dict(**kwargs)
				kwargs['ambigious'] = 2
			else:
				pass
		super(VimRenderer, self).__init__(**kwargs)
		self.vim_cls = vim_cls
		self.theme_reqs_dict = self.vim_cls.theme_to_reqs_dict(self.theme)
		self.theme_dict = {
			'theme': self.theme,
			'reqs_dict': self.theme_reqs_dict,
		}
		self.hl_groups = {}
		self.prev_highlight = None
		self.strwidth_error_name = register_strwidth_error(self.strwidth)
		self.encoding = get_vim_encoding(self.vim)
		self.uses_vim_python = True
		if not is_old_vim:
			self.theme_selector = self.vim_cls.compile_themes_getter(
				self.local_themes, vim_funcs, vim)
		self.is_old_vim = is_old_vim
		self.vim_funcs = vim_funcs
		self.themelambda = None
		self.segment_info = self.segment_info.copy()
		self.segment_info.update(vim=self.vim, environ=VimEnviron(self.vim))

	def shutdown(self):
		self.theme.shutdown()
		for _, theme in self.local_themes:
			if 'theme' in theme:
				theme['theme'].shutdown()

	def add_local_theme(self, matcher, theme):
		if matcher in (m for m, _ in self.local_themes):
			raise KeyError('There is already a local theme with given matcher')
		self.local_themes.append((matcher, theme))

	def get_theme(self, matcher_info):
		return matcher_info['theme']

	def get_segment_info(self, segment_info, mode):
		return segment_info or self.segment_info

	def render(self, input=None, themenr=None, window_id=None, window=None, winnr=None, is_tabline=False):
		# def render(self, window=None, window_id=None, winnr=None, 
		# is_tabline=False, local_theme=None):
		'''Render all segments.'''
		segment_info = self.segment_info.copy()
		if not themenr:
			if self.themelambda is not None:
				themenr = self.themelambda(self.pl, segment_info)

		buffer = window.buffer if window else None
		tabpage = current_tabpage(self.vim, self.is_old_vim, input)

		segment_info.update(
			window=window,
			window_id=window_id,
			winnr=winnr,
			buffer=buffer,
			tabpage=tabpage,
			encoding=self.encoding,
		)
		segment_info['tabnr'] = tabpage.number
		if input and 'buffer_number' in input:
			segment_info['bufnr'] = input['buffer_number']
		else:
			segment_info['bufnr'] = buffer and buffer.number

		if themenr is None:
			theme = self.theme_selector(
				pl=self.pl,
				matcher_info=segment_info,
				theme=self.theme_dict,
				buffer=buffer,
				window=window,
				tabpage=tabpage,
			)
		elif themenr == 0:
			theme = self.theme_dict
		else:
			theme = self.local_themes[themenr - 1][1]

		if input is None:
			try:
				input = theme['input_getter'](buffer, window, tabpage)
			except KeyError:
				theme['input_getter'] = self.vim_cls.compile_reqs_dict(
					theme['reqs_dict'], self.vim_funcs, self.vim,
					tabscope=theme.get('is_tabline'))
				input = theme['input_getter'](buffer, window, tabpage)

		if is_tabline or winnr == input['current_window_number']:
			mode = input['mode']
			mode = mode_translations.get(mode, mode)
		else:
			mode = 'nc'

		segment_info.update(input=input, mode=mode)
		winwidth = segment_info['input']['available_width']

		statusline = super(VimRenderer, self).render(
			mode=mode,
			width=winwidth,
			segment_info=segment_info,
			matcher_info=theme,
		)
		statusline = statusline.encode(self.encoding, self.strwidth_error_name)
		return statusline

	def reset_highlight(self):
		self.hl_groups.clear()

	def hlstyle(self, fg=None, bg=None, attrs=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it’s added to the vim highlight group.
		'''
		# In order not to hit E541 two consequent identical highlighting 
		# specifiers may be squashed into one.
		attrs = attrs or 0  # Normalize `attrs`
		if (fg, bg, attrs) == self.prev_highlight:
			return ''
		self.prev_highlight = (fg, bg, attrs)

		# We don’t need to explicitly reset attributes in vim, so skip those 
		# calls
		if not attrs and not bg and not fg:
			return ''

		if not (fg, bg, attrs) in self.hl_groups:
			hl_group = {
				'ctermfg': 'NONE',
				'guifg': None,
				'ctermbg': 'NONE',
				'guibg': None,
				'attrs': ['NONE'],
				'name': '',
			}
			if fg is not None and fg is not False:
				hl_group['ctermfg'] = fg[0]
				hl_group['guifg'] = fg[1]
			if bg is not None and bg is not False:
				hl_group['ctermbg'] = bg[0]
				hl_group['guibg'] = bg[1]
			if attrs:
				hl_group['attrs'] = []
				if attrs & ATTR_BOLD:
					hl_group['attrs'].append('bold')
				if attrs & ATTR_ITALIC:
					hl_group['attrs'].append('italic')
				if attrs & ATTR_UNDERLINE:
					hl_group['attrs'].append('underline')
			hl_group['name'] = (
				'Pl_'
				+ str(hl_group['ctermfg']) + '_'
				+ str(hl_group['guifg']) + '_'
				+ str(hl_group['ctermbg']) + '_'
				+ str(hl_group['guibg']) + '_'
				+ ''.join(hl_group['attrs'])
			)
			self.hl_groups[(fg, bg, attrs)] = hl_group
			self.vim.command('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attrs} gui={attrs}'.format(
				group=hl_group['name'],
				ctermfg=hl_group['ctermfg'],
				guifg='#{0:06x}'.format(hl_group['guifg']) if hl_group['guifg'] is not None else 'NONE',
				ctermbg=hl_group['ctermbg'],
				guibg='#{0:06x}'.format(hl_group['guibg']) if hl_group['guibg'] is not None else 'NONE',
				attrs=','.join(hl_group['attrs']),
			))
		return '%#' + self.hl_groups[(fg, bg, attrs)]['name'] + '#'


renderer = VimRenderer
