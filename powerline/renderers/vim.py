# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals

from powerline.bindings.vim import vim_get_func, environ, current_tabpage
from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE
from powerline.theme import Theme

import vim
import sys


try:
	from __builtin__ import unichr as chr
except ImportError:
	pass


vim_mode = vim_get_func('mode', rettype=str)
mode_translations = {
	chr(ord('V') - 0x40): '^V',
	chr(ord('S') - 0x40): '^S',
}


class VimRenderer(Renderer):
	'''Powerline vim segment renderer.'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('%')] = '%%'

	segment_info = Renderer.segment_info.copy()
	segment_info.update(environ=environ)

	def __init__(self, *args, **kwargs):
		if not hasattr(vim, 'strwidth'):
			# Hope nobody want to change this at runtime
			if vim.eval('&ambiwidth') == 'double':
				kwargs = dict(**kwargs)
				kwargs['ambigious'] = 2
		super(VimRenderer, self).__init__(*args, **kwargs)
		self.hl_groups = {}

	def shutdown(self):
		self.theme.shutdown()
		for match in self.local_themes.values():
			if 'theme' in match:
				match['theme'].shutdown()

	def add_local_theme(self, matcher, theme):
		if matcher in self.local_themes:
			raise KeyError('There is already a local theme with given matcher')
		self.local_themes[matcher] = theme

	def get_matched_theme(self, match):
		try:
			return match['theme']
		except KeyError:
			match['theme'] = Theme(theme_config=match['config'], main_theme_config=self.theme_config, **self.theme_kwargs)
			return match['theme']

	def get_theme(self, matcher_info):
		if matcher_info is None:
			return self.get_matched_theme(self.local_themes[None])
		for matcher in self.local_themes.keys():
			if matcher and matcher(matcher_info):
				return self.get_matched_theme(self.local_themes[matcher])
		else:
			return self.theme

	if hasattr(vim, 'strwidth'):
		if sys.version_info < (3,):
			@staticmethod
			def strwidth(string):
				# Does not work with tabs, but neither is strwidth from default 
				# renderer
				return vim.strwidth(string.encode('utf-8'))
		else:
			@staticmethod  # NOQA
			def strwidth(string):
				return vim.strwidth(string)

	def get_segment_info(self, segment_info, mode):
		return segment_info or self.segment_info

	def render(self, window=None, window_id=None, winnr=None):
		'''Render all segments.'''
		segment_info = self.segment_info.copy()
		if window is not None:
			if window is vim.current.window:
				mode = vim_mode(1)
				mode = mode_translations.get(mode, mode)
			else:
				mode = 'nc'
			segment_info.update(
				window=window,
				mode=mode,
				window_id=window_id,
				winnr=winnr,
				buffer=window.buffer,
				tabpage=current_tabpage(),
			)
			segment_info['tabnr'] = segment_info['tabpage'].number
			segment_info['bufnr'] = segment_info['buffer'].number
			winwidth = segment_info['window'].width
			matcher_info = segment_info
		else:
			mode = None
			winwidth = int(vim.eval('&columns'))
			matcher_info = None
		statusline = super(VimRenderer, self).render(
			mode=mode,
			width=winwidth,
			segment_info=segment_info,
			matcher_info=matcher_info,
		)
		return statusline

	def reset_highlight(self):
		self.hl_groups.clear()

	def hlstyle(self, fg=None, bg=None, attr=None):
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
				'guifg': None,
				'ctermbg': 'NONE',
				'guibg': None,
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
				if attr & ATTR_BOLD:
					hl_group['attr'].append('bold')
				if attr & ATTR_ITALIC:
					hl_group['attr'].append('italic')
				if attr & ATTR_UNDERLINE:
					hl_group['attr'].append('underline')
			hl_group['name'] = (
				'Pl_'
				+ str(hl_group['ctermfg']) + '_'
				+ str(hl_group['guifg']) + '_'
				+ str(hl_group['ctermbg']) + '_'
				+ str(hl_group['guibg']) + '_'
				+ ''.join(hl_group['attr'])
			)
			self.hl_groups[(fg, bg, attr)] = hl_group
			vim.command('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
				group=hl_group['name'],
				ctermfg=hl_group['ctermfg'],
				guifg='#{0:06x}'.format(hl_group['guifg']) if hl_group['guifg'] is not None else 'NONE',
				ctermbg=hl_group['ctermbg'],
				guibg='#{0:06x}'.format(hl_group['guibg']) if hl_group['guibg'] is not None else 'NONE',
				attr=','.join(hl_group['attr']),
			))
		return '%#' + self.hl_groups[(fg, bg, attr)]['name'] + '#'


renderer = VimRenderer
