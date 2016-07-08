# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import Theme
from powerline.renderers.shell import PromptRenderer


class IPythonRenderer(PromptRenderer):
	'''Powerline ipython segment renderer.'''
	def get_segment_info(self, segment_info, mode):
		r = self.segment_info.copy()
		r['ipython'] = segment_info
		return r

	def get_theme(self, matcher_info):
		if matcher_info == 'in':
			return self.theme
		else:
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

	def shutdown(self):
		self.theme.shutdown()
		for match in self.local_themes.values():
			if 'theme' in match:
				match['theme'].shutdown()
