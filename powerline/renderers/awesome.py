# -*- coding: utf-8 -*-

from powerline.renderer import Renderer


class AwesomeRenderer(Renderer):
	'''Powerline Awesome WM segment renderer.'''

	def hl(self, contents=None, fg=None, bg=None, attr=None):
		'''Highlight a segment.'''
		# We don't need to explicitly reset attributes, so skip those calls
		if not contents or (not attr and not bg and not fg):
			return ''
		awesome_attr = []
		if fg is not None:
			if fg is not False and fg[1] is not False:
				awesome_attr += ['foreground="#{0:06x}"'.format(fg[1])]
		if bg is not None:
			if bg is not False and bg[1] is not False:
				awesome_attr += ['background="#{0:06x}"'.format(bg[1])]
		if attr is not None and attr is not False:
			if attr & Renderer.ATTR_BOLD:
				awesome_attr += ['font_weight="bold"']
			if attr & Renderer.ATTR_ITALIC:
				awesome_attr += ['font_style="italic"']
			if attr & Renderer.ATTR_UNDERLINE:
				awesome_attr += ['underline="single"']
		return '<span ' + ' '.join(awesome_attr) + '>' + contents + '</span>'
