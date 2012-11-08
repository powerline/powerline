#!/usr/bin/env python

from lib.core import Segment
from lib.renderers import SegmentRenderer


class TerminalSegmentRenderer(SegmentRenderer):
	'''Powerline terminal segment renderer.
	'''
	def fg(col):
		'''Return ANSI escape code for foreground colors.

		If no color is provided, the color is reset to the terminal default.
		'''
		if col:
			return '[38;5;{0}m'.format(col)
		else:
			return '[39m'

	def bg(col):
		'''Return ANSI escape code for background colors.

		If no color is provided, the color is reset to the terminal default.
		'''
		if col:
			return '[48;5;{0}m'.format(col)
		else:
			return '[49m'

	def attr(attrs):
		'''Return ANSI escape code for attributes.

		Accepts a flag with attributes defined in Segment.

		If no attributes are provided, the attributes are reset to the terminal
		defaults.
		'''
		if not attrs:
			return '[22m'

		ansi_attrs = []
		if attrs & Segment.ATTR_BOLD:
			ansi_attrs.append('1')

		if ansi_attrs:
			return '[{0}m'.format(';'.join(ansi_attrs))

		return ''
