# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals

from powerline.renderer import Renderer
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
	tmux_escape = False
	screen_escape = False

	character_translations = Renderer.character_translations.copy()

	def hlstyle(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it's added to the ANSI escape code.
		'''
		ansi = [0]
		if fg is not None:
			if fg is False or fg[0] is False:
				ansi += [39]
			else:
				if self.term_truecolor:
					ansi += [38, 2] + list(int_to_rgb(fg[1]))
				else:
					ansi += [38, 5, fg[0]]
		if bg is not None:
			if bg is False or bg[0] is False:
				ansi += [49]
			else:
				if self.term_truecolor:
					ansi += [48, 2] + list(int_to_rgb(bg[1]))
				else:
					ansi += [48, 5, bg[0]]
		if attr is not None:
			if attr is False:
				ansi += [22]
			else:
				if attr & ATTR_BOLD:
					ansi += [1]
				elif attr & ATTR_ITALIC:
					# Note: is likely not to work or even be inverse in place of
					# italic. Omit using this in colorschemes.
					ansi += [3]
				elif attr & ATTR_UNDERLINE:
					ansi += [4]
		r = '\033[{0}m'.format(';'.join(str(attr) for attr in ansi))
		if self.tmux_escape:
			r = '\033Ptmux;' + r.replace('\033', '\033\033') + '\033\\'
		elif self.screen_escape:
			r = '\033P' + r.replace('\033', '\033\033') + '\033\\'
		return self.escape_hl_start + r + self.escape_hl_end


renderer = ShellRenderer
