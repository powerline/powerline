# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals

from powerline.renderers.zsh_prompt import ZshPromptRenderer


class TcshPromptRenderer(ZshPromptRenderer):
	'''Powerline tcsh prompt segment renderer.'''
	character_translations = ZshPromptRenderer.character_translations.copy()
	character_translations[ord('%')] = '%%'
	character_translations[ord('\\')] = '\\\\'
	character_translations[ord('^')] = '\\^'


renderer = TcshPromptRenderer
