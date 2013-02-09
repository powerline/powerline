# -*- coding: utf-8 -*-

from powerline.renderer import Renderer


class PangoMarkupRenderer(Renderer):
	'''Powerline Pango markup segment renderer.'''

	@staticmethod
	def hlstyle(*args, **kwargs):
		# We don't need to explicitly reset attributes, so skip those calls
		return ''

	def hl(self, contents, fg=None, bg=None, attr=None):
		'''Highlight a segment.'''
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
