# -*- coding: utf-8 -*-

from powerline.renderer import Renderer


class TmuxRenderer(Renderer):
	'''Powerline tmux segment renderer.'''
	def hl(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.'''
		tmux_attr = []
		if fg is not None:
			if fg[0] is False:
				tmux_attr += ['fg=default']
			else:
				tmux_attr += ['fg=colour' + str(fg[0])]
		if bg is not None:
			if bg[0] is False:
				tmux_attr += ['bg=default']
			else:
				tmux_attr += ['bg=colour' + str(bg[0])]
		if attr is not None:
			if attr is False:
				tmux_attr += ['nobold', 'noitalics', 'nounderscore']
			else:
				if attr & Renderer.ATTR_BOLD:
					tmux_attr += ['bold']
				else:
					tmux_attr += ['nobold']
				if attr & Renderer.ATTR_ITALIC:
					tmux_attr += ['italics']
				else:
					tmux_attr += ['noitalics']
				if attr & Renderer.ATTR_UNDERLINE:
					tmux_attr += ['underscore']
				else:
					tmux_attr += ['nounderscore']
		return '#[' + ','.join(tmux_attr) + ']'
