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

	def do_render(self, **kwargs):
		ret = super(TcshPromptRenderer, self).do_render(**kwargs)
		nbsp = self.character_translations.get(ord(' '), ' ')
		end = self.hlstyle()
		assert not ret or ret.endswith(end)
		if ret.endswith(nbsp + end):
			# Exchange nbsp and highlight end because tcsh removes trailing 
			# %{%} part of the prompt for whatever reason
			ret = ret[:-(len(nbsp) + len(end))] + end + nbsp
		else:
			# We *must* end prompt with non-%{%} sequence for the reasons 
			# explained above. So add nbsp if it is not already there.
			ret += nbsp
		return ret


renderer = TcshPromptRenderer
