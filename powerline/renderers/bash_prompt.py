# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals

from powerline.renderers.shell import ShellRenderer


class BashPromptRenderer(ShellRenderer):
	'''Powerline bash prompt segment renderer.'''
	escape_hl_start = '\['
	escape_hl_end = '\]'

	character_translations = ShellRenderer.character_translations.copy()
	character_translations[ord('$')] = '\\$'
	character_translations[ord('`')] = '\\`'
	character_translations[ord('\\')] = '\\\\'


renderer = BashPromptRenderer
