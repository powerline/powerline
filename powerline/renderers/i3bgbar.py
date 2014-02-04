# vim:fileencoding=utf-8:noet

from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE
import json

class i3bgbarRenderer(Renderer):
	'''i3bgbar Segment Renderer'''

	@staticmethod
	def hlstyle(*args, **kwargs):
		# We don't need to explicitly reset attributes, so skip those calls
		return ''

	def hl(self, contents, fg=None, bg=None, attr=None):
		'''Highlight a segment.'''

		segment = { "full_text": contents, "separator": False, "separator_block_width": 0 } # no seperators

		if fg is not None:
			if fg is not False and fg[1] is not False:
				segment['color'] = "#{0:06x}".format(fg[1])
		if bg is not None:
			if bg is not False and bg[1] is not False:
				segment['background_color'] = "#{0:06x}".format(bg[1])
		"""
		if attr is not None and attr is not False:
			if attr & ATTR_BOLD:
				awesome_attr += ['font_weight="bold"']
			if attr & ATTR_ITALIC:
				awesome_attr += ['font_style="italic"']
			if attr & ATTR_UNDERLINE:
				awesome_attr += ['underline="single"']
		"""
		return json.dumps( segment ) + ",\n"


renderer = i3bgbarRenderer
