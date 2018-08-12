# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import json

from powerline.renderer import Renderer


class I3barRenderer(Renderer):
	'''I3bar Segment Renderer.

	Currently works only for i3bgbar (i3 bar with custom patches).
	'''

	@staticmethod
	def hlstyle(*args, **kwargs):
		# We don’t need to explicitly reset attributes, so skip those calls
		return ''

	def hl(self, contents, fg=None, bg=None, attrs=None):
		segment = {
			'full_text': contents,
			'separator': False,
			'separator_block_width': 0,  # no seperators
		}

		if fg is not None:
			if fg is not False and fg[1] is not False:
				segment['color'] = '#{0:06x}'.format(fg[1])
		if bg is not None:
			if bg is not False and bg[1] is not False:
				segment['background'] = '#{0:06x}'.format(bg[1])
		return json.dumps(segment) + ','


renderer = I3barRenderer
