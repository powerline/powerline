# -*- coding: utf-8 -*-

import os

from powerline.renderer import Renderer


class TerminalRenderer(Renderer):
	'''Powerline terminal segment renderer.'''
	_color_templates = {
		'default': '[{code}m',
		'bash': '\[[{code}m\]',
		'zsh': '%{{[{code}m%}}',
	}

	def __init__(self, *args, **kwargs):
		super(TerminalRenderer, self).__init__(*args, **kwargs)
		shell = os.path.basename(os.environ.get('SHELL', 'default'))
		self.color_template = self._color_templates[shell]

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
				if attr & Renderer.ATTR_BOLD:
					ansi += [1]
		return self.color_template.format(code=';'.join(str(attr) for attr in ansi))
