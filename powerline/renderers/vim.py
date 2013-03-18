# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

from powerline.bindings.vim import vim_get_func
from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE
from powerline.theme import Theme

import vim


vim_mode = vim_get_func('mode')
vim_getwinvar = vim_get_func('getwinvar')
vim_setwinvar = vim_get_func('setwinvar')
mode_translations = {
	chr(ord('V') - 0x40): '^V',
	chr(ord('S') - 0x40): '^S',
}


class VimRenderer(Renderer):
	'''Powerline vim segment renderer.'''

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

	def get_theme(self, matcher_info):
		for matcher in self.local_themes.keys():
			if matcher(matcher_info):
				match = self.local_themes[matcher]
				if 'config' in match:
					match['theme'] = Theme(theme_config=match.pop('config'), top_theme_config=self.theme_config, **self.theme_kwargs)
				return match['theme']
		else:
			return self.theme

	if hasattr(vim, 'strwidth'):
		@staticmethod
		def strwidth(string):
			# Does not work with tabs, but neither is strwidth from default 
			# renderer
			return vim.strwidth(string.encode('utf-8'))

	def render(self, window_id, winidx, current):
		'''Render all segments.

		This method handles replacing of the percent placeholder for vim
		statuslines, and it caches segment contents which are retrieved and
		used in non-current windows.
		'''
		if current:
			mode = vim_mode(1)
			mode = mode_translations.get(mode, mode)
		else:
			mode = 'nc'
		segment_info = {
			'window': vim.windows[winidx],
			'mode': mode,
			'window_id': window_id,
			}
		segment_info['buffer'] = segment_info['window'].buffer
		segment_info['bufnr'] = segment_info['buffer'].number
		winwidth = segment_info['window'].width
		statusline = super(VimRenderer, self).render(mode, winwidth, segment_info=segment_info, matcher_info=segment_info)
		return statusline

	def reset_highlight(self):
		self.hl_groups.clear()

	@staticmethod
	def escape(string):
		return string.replace('%', '%%')

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
					guifg='#{0:06x}'.format(hl_group['guifg']) if hl_group['guifg'] is not None else 'NONE',
					ctermbg=hl_group['ctermbg'],
					guibg='#{0:06x}'.format(hl_group['guibg']) if hl_group['guibg'] is not None else 'NONE',
					attr=','.join(hl_group['attr']),
				))
		return '%#' + self.hl_groups[(fg, bg, attr)]['name'] + '#'


renderer = VimRenderer
