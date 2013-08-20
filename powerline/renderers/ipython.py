# vim:fileencoding=utf-8:noet

from powerline.renderers.shell import ShellRenderer
from powerline.theme import Theme


class IpythonRenderer(ShellRenderer):
	'''Powerline ipython segment renderer.'''
	escape_hl_start = '\x01'
	escape_hl_end = '\x02'

	def get_segment_info(self, segment_info):
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
				match['theme'] = Theme(theme_config=match['config'], top_theme_config=self.theme_config, **self.theme_kwargs)
				return match['theme']

	def shutdown(self):
		self.theme.shutdown()
		for match in self.local_themes.values():
			if 'theme' in match:
				match['theme'].shutdown()


renderer = IpythonRenderer
