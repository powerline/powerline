# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class BashPromptRenderer(ShellRenderer):
	'''Powerline bash prompt segment renderer.'''
	def hlstyle(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		Returns the default ShellRenderer escape sequence with \[...\] wrapped
		around it (required in bash prompts).
		'''
		return '\[' + super(BashPromptRenderer, self).hlstyle(fg, bg, attr) + '\]'

	@staticmethod
	def escape(string):
		return string.replace('\\', '\\\\').replace('$', '\\$').replace('`', '\\`')
