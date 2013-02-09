# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class ZshPromptRenderer(ShellRenderer):
	'''Powerline zsh prompt segment renderer.'''
	def hlstyle(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.

		Returns the default ShellRenderer escape sequence with %{...%} wrapped
		around it (required in zsh prompts).
		'''
		return '%{' + super(ZshPromptRenderer, self).hlstyle(None, fg, bg, attr) + '%}'

	@staticmethod
	def escape(string):
		return string.replace('%', '%%').replace('\\', '\\\\')
