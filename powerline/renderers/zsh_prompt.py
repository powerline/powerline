# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class ZshPromptRenderer(ShellRenderer):
	'''Powerline zsh prompt segment renderer.'''
	def hl(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		Returns the default ShellRenderer escape sequence with %{...%} wrapped
		around it (required in zsh prompts).
		'''
		return '%{' + super(ZshPromptRenderer, self).hl(fg, bg, attr) + '%}'
