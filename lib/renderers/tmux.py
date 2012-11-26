#!/usr/bin/env python

from lib.core import Powerline
from lib.renderers import SegmentRenderer


class TmuxSegmentRenderer(SegmentRenderer):
	'''Powerline tmux segment renderer.
	'''
	def hl(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.
		'''
		tmux_attr = []

		if fg is not None:
			tmux_attr += ['fg=colour' + str(fg[0])]

		if bg is not None:
			tmux_attr += ['bg=colour' + str(bg[0])]

		if attr is not None:
			if attr is False:
				tmux_attr += ['nobold', 'noitalics', 'nounderscore']
			else:
				if attr & Powerline.ATTR_BOLD:
					tmux_attr += ['bold']
				else:
					tmux_attr += ['nobold']
				if attr & Powerline.ATTR_ITALIC:
					tmux_attr += ['italics']
				else:
					tmux_attr += ['noitalics']
				if attr & Powerline.ATTR_UNDERLINE:
					tmux_attr += ['underscore']
				else:
					tmux_attr += ['nounderscore']

		return '#[' + ','.join(tmux_attr) + ']'
