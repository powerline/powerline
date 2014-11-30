# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderers.shell.zsh import ZshPromptRenderer


class TcshPromptRenderer(ZshPromptRenderer):
	'''Powerline tcsh prompt segment renderer.'''
	character_translations = ZshPromptRenderer.character_translations.copy()
	character_translations[ord('%')] = '%%'
	character_translations[ord('\\')] = '\\\\'
	character_translations[ord('^')] = '\\^'
	character_translations[ord('!')] = '\\!'


renderer = TcshPromptRenderer
