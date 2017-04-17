# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell import ShellRenderer


ESCAPE_CHAR = '\001'


class KshPromptRenderer(ShellRenderer):
	'''Powerline bash prompt segment renderer.'''
	escape_hl_start = '\001'
	escape_hl_end = '\001'

	def render(self, *args, **kwargs):
		return '\001\r' + super(KshPromptRenderer, self).render(*args, **kwargs)


renderer = KshPromptRenderer
