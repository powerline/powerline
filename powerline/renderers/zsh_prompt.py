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

	old_widths = {}

	def render(self, segment_info, *args, **kwargs):
		client_id = segment_info.get('client_id')
		key = (client_id, kwargs.get('side'))
		kwargs = kwargs.copy()
		width = kwargs.pop('width', None)
		local_theme = segment_info.get('local_theme')
		if client_id and local_theme:
			output_raw = False
			try:
				width = self.old_widths[key]
			except KeyError:
				pass
		else:
			output_raw = True
		ret = super(ShellRenderer, self).render(
			output_raw=output_raw,
			width=width,
			matcher_info=local_theme,
			segment_info=segment_info,
			*args, **kwargs
		)
		if output_raw:
			self.old_widths[key] = len(ret[1])
			ret = ret[0]
		return ret

	def get_theme(self, matcher_info):
		if not matcher_info:
			return self.theme
		match = self.local_themes[matcher_info]
		try:
			return match['theme']
		except KeyError:
			match['theme'] = Theme(
				theme_config=match['config'],
				top_theme_config=self.theme_config,
				**self.theme_kwargs
			)
			return match['theme']


renderer = ZshPromptRenderer
