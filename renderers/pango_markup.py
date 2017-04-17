# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from xml.sax.saxutils import escape as _escape

from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


class PangoMarkupRenderer(Renderer):
	'''Powerline Pango markup segment renderer.'''

	@staticmethod
	def hlstyle(*args, **kwargs):
		# We don’t need to explicitly reset attributes, so skip those calls
		return ''

	def hl(self, contents, fg=None, bg=None, attrs=None):
		'''Highlight a segment.'''
		awesome_attr = []
		if fg is not None:
			if fg is not False and fg[1] is not False:
				awesome_attr += ['foreground="#{0:06x}"'.format(fg[1])]
		if bg is not None:
			if bg is not False and bg[1] is not False:
				awesome_attr += ['background="#{0:06x}"'.format(bg[1])]
		if attrs is not None and attrs is not False:
			if attrs & ATTR_BOLD:
				awesome_attr += ['font_weight="bold"']
			if attrs & ATTR_ITALIC:
				awesome_attr += ['font_style="italic"']
			if attrs & ATTR_UNDERLINE:
				awesome_attr += ['underline="single"']
		return '<span ' + ' '.join(awesome_attr) + '>' + contents + '</span>'

	escape = staticmethod(_escape)


renderer = PangoMarkupRenderer
