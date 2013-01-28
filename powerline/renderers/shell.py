# -*- coding: utf-8 -*-

from powerline.renderer import Renderer


class ShellRenderer(Renderer):
	'''Powerline shell segment renderer.'''
	def hl(self, contents=None, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it's added to the ANSI escape code.
		'''
		ansi = []
		if fg is not None:
			if fg is False or fg[0] is False:
				ansi += [39]
			else:
				if self.TERM_24BIT_COLORS:
					ansi += [38, 2] + list(self._int_to_rgb(fg[1]))
				else:
					ansi += [38, 5, fg[0]]
		if bg is not None:
			if bg is False or bg[0] is False:
				ansi += [49]
			else:
				if self.TERM_24BIT_COLORS:
					ansi += [48, 2] + list(self._int_to_rgb(bg[1]))
				else:
					ansi += [48, 5, bg[0]]
		if attr is not None:
			if attr is False:
				ansi += [22]
			else:
				if attr & Renderer.ATTR_BOLD:
					ansi += [1]
		return '[{0}m'.format(';'.join(str(attr) for attr in ansi)) + (contents or u'')

	@staticmethod
	def escape(string):
		return string.replace('\\', '\\\\')
