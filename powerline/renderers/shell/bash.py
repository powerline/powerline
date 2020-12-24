# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell import ShellRenderer


class BashPromptRenderer(ShellRenderer):
	'''Powerline bash prompt segment renderer.'''
	escape_hl_start = r'\['
	escape_hl_end = r'\]'

	character_translations = ShellRenderer.character_translations.copy()
	character_translations[ord('$')] = '\\$'
	character_translations[ord('`')] = '\\`'
	character_translations[ord('\\')] = '\\\\'


renderer = BashPromptRenderer
