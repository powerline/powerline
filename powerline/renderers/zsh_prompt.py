# -*- coding: utf-8 -*-

from powerline.renderers.shell import ShellRenderer


class ZshPromptRenderer(ShellRenderer):
	'''Powerline zsh prompt segment renderer.'''
	def hl(self, *args, **kwargs):
		'''Highlight a segment.

		Returns the default ShellRenderer escape sequence with %{...%} wrapped
		around it (required in zsh prompts).
		'''
		return '%{' + super(ZshPromptRenderer, self).hl(*args, **kwargs) + '%}'

	@staticmethod
	def escape(string):
		return string.replace('%', '%%').replace('\\', '\\\\')
