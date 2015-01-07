# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderer import Renderer
from powerline.theme import Theme
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


def int_to_rgb(num):
	r = (num >> 16) & 0xff
	g = (num >> 8) & 0xff
	b = num & 0xff
	return r, g, b


class ShellRenderer(Renderer):
	'''Powerline shell segment renderer.'''
	escape_hl_start = ''
	escape_hl_end = ''
	term_truecolor = False
	term_escape_style = 'auto'
	tmux_escape = False
	screen_escape = False

	character_translations = Renderer.character_translations.copy()

	def __init__(self, old_widths=None, **kwargs):
		super(ShellRenderer, self).__init__(**kwargs)
		self.old_widths = old_widths if old_widths is not None else {}

	def render(self, segment_info, **kwargs):
		local_theme = segment_info.get('local_theme')
		return super(ShellRenderer, self).render(
			matcher_info=local_theme,
			segment_info=segment_info,
			**kwargs
		)

	def do_render(self, output_width, segment_info, side, theme, width=None, **kwargs):
		if self.term_escape_style == 'auto':
			if segment_info['environ'].get('TERM') == 'fbterm':
				self.used_term_escape_style = 'fbterm'
			else:
				self.used_term_escape_style = 'xterm'
		else:
			self.used_term_escape_style = self.term_escape_style
		if isinstance(segment_info, dict):
			client_id = segment_info.get('client_id')
		else:
			client_id = None
		if client_id is not None:
			local_key = (client_id, side, None if theme is self.theme else id(theme))
			key = (client_id, side, None)
			did_width = False
			if local_key[-1] != key[-1] and side == 'left':
				try:
					width = self.old_widths[key]
				except KeyError:
					pass
				else:
					did_width = True
			if not did_width and width is not None:
				if theme.cursor_space_multiplier is not None:
					width = int(width * theme.cursor_space_multiplier)
				elif theme.cursor_columns:
					width -= theme.cursor_columns

				if side == 'right':
					try:
						width -= self.old_widths[(client_id, 'left', local_key[-1])]
					except KeyError:
						pass
		res = super(ShellRenderer, self).do_render(
			output_width=True,
			width=width,
			theme=theme,
			segment_info=segment_info,
			side=side,
			**kwargs
		)
		if client_id is not None:
			self.old_widths[local_key] = res[-1]
		ret = res if output_width else res[:-1]
		if len(ret) == 1:
			return ret[0]
		else:
			return ret

	def hlstyle(self, fg=None, bg=None, attrs=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it’s added to the ANSI escape code.
		'''
		ansi = [0]
		is_fbterm = self.used_term_escape_style == 'fbterm'
		term_truecolor = not is_fbterm and self.term_truecolor
		if fg is not None:
			if fg is False or fg[0] is False:
				ansi += [39]
			else:
				if term_truecolor:
					ansi += [38, 2] + list(int_to_rgb(fg[1]))
				else:
					ansi += [38, 5, fg[0]]
		if bg is not None:
			if bg is False or bg[0] is False:
				ansi += [49]
			else:
				if term_truecolor:
					ansi += [48, 2] + list(int_to_rgb(bg[1]))
				else:
					ansi += [48, 5, bg[0]]
		if attrs is not None:
			if attrs is False:
				ansi += [22]
			else:
				if attrs & ATTR_BOLD:
					ansi += [1]
				elif attrs & ATTR_ITALIC:
					# Note: is likely not to work or even be inverse in place of
					# italic. Omit using this in colorschemes.
					ansi += [3]
				elif attrs & ATTR_UNDERLINE:
					ansi += [4]
		if is_fbterm:
			r = []
			while ansi:
				cur_ansi = ansi.pop(0)
				if cur_ansi == 38:
					ansi.pop(0)
					r.append('\033[1;{0}}}'.format(ansi.pop(0)))
				elif cur_ansi == 48:
					ansi.pop(0)
					r.append('\033[2;{0}}}'.format(ansi.pop(0)))
				else:
					r.append('\033[{0}m'.format(cur_ansi))
			r = ''.join(r)
		else:
			r = '\033[{0}m'.format(';'.join(str(attr) for attr in ansi))
		if self.tmux_escape:
			r = '\033Ptmux;' + r.replace('\033', '\033\033') + '\033\\'
		elif self.screen_escape:
			r = '\033P' + r.replace('\033', '\033\033') + '\033\\'
		return self.escape_hl_start + r + self.escape_hl_end

	def get_theme(self, matcher_info):
		if not matcher_info:
			return self.theme
		match = self.local_themes[matcher_info]
		try:
			return match['theme']
		except KeyError:
			match['theme'] = Theme(
				theme_config=match['config'],
				main_theme_config=self.theme_config,
				**self.theme_kwargs
			)
			return match['theme']


renderer = ShellRenderer
