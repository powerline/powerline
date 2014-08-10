# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals

from powerline.renderers.shell import ShellRenderer
from powerline.theme import Theme


class ZshPromptRenderer(ShellRenderer):
	'''Powerline zsh prompt segment renderer.'''
	escape_hl_start = '%{'
	escape_hl_end = '%}'

	character_translations = ShellRenderer.character_translations.copy()
	character_translations[ord('%')] = '%%'

	def get_theme(self, matcher_info):
		if not matcher_info:
			return self.theme
		match = self.local_themes[matcher_info]
		try:
			return match['theme']
		except KeyError:
			match['theme'] = Theme(
				theme_config=match['config'],
				main_theme_config=self.theme_config,
				**self.theme_kwargs
			)
			return match['theme']


renderer = ZshPromptRenderer
