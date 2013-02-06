# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class BashPromptRenderer(ShellRenderer):
	'''Powerline bash prompt segment renderer.'''
	def hl(self, contents=None, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		Returns the default ShellRenderer escape sequence with \[...\] wrapped
		around it (required in bash prompts).
		'''
		return '\[' + super(BashPromptRenderer, self).hl(None, fg, bg, attr) + '\]' + (contents or u'')
