#!/usr/bin/env python

from lib.core import Powerline
from lib.renderers import SegmentRenderer


class TerminalSegmentRenderer(SegmentRenderer):
	'''Powerline terminal segment renderer.
	'''
	def hl(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		If an argument is None, the argument is ignored. If an argument is
		False, the argument is reset to the terminal defaults. If an argument
		is a valid color or attribute, it's added to the ANSI escape code.
		'''
		ansi = []

		if fg is not None:
			if fg[0] is False:
				ansi += [39]
			else:
				ansi += [38, 5, fg[0]]

		if bg is not None:
			if bg[0] is False:
				ansi += [49]
			else:
				ansi += [48, 5, bg[0]]

		if attr is not None:
			if attr is False:
				ansi += [22]
			else:
				if attr & Powerline.ATTR_BOLD:
					ansi += [1]

		return '[{0}m'.format(';'.join(str(attr) for attr in ansi))
