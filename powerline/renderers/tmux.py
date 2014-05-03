# vim:fileencoding=utf-8:noet
from __future__ import absolute_import, unicode_literals
from subprocess import call

from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


class TmuxRenderer(Renderer):
	'''Powerline tmux segment renderer.'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('#')] = '##[]'

	def render(self, *args, **kwargs):
		self._set_global_tmux_options()
		return super(TmuxRenderer, self).render(*args, **kwargs)

	def hlstyle(self, fg=None, bg=None, attr=None):
		'''Highlight a segment.'''
		# We don't need to explicitly reset attributes, so skip those calls
		if not any((attr, bg, fg)): return ''
		return '#[' + ','.join(self._get_tmux_attributes(fg, bg, attr)) + ']'

	def get_segment_info(self, segment_info, mode):
		new_segment_info = self.segment_info.copy()
		if segment_info:
			new_segment_info.update(segment_info)
		if 'pane_id' in new_segment_info:
			self._add_get_cwd_to_segment_info(new_segment_info)
		new_segment_info['mode'] = mode
		return new_segment_info

	@staticmethod
	def _get_color_string(color, color_type):
		if color is False or color[0] is False:
			return '{0}=default'.format(color_type)
		else:
			return '{color_type}=colour{color}'.format(color_type=color_type,
													   color=color[0])

	def _get_tmux_attributes(self, fg=None, bg=None, attr=None):
		if fg is not None:
			yield self._get_color_string(fg, 'fg')
			yield self._get_color_string(bg, 'bg')
		if attr is not None:
			attr = attr or 0 # Converts False to 0
			yield 'bold' if attr & ATTR_BOLD else 'nobold'
			yield 'italics' if attr & ATTR_ITALIC else 'noitalics'
			yield 'underscore' if attr & ATTR_UNDERLINE else 'nounderscore'

	@staticmethod
	def _set_tmux_option(option, value):
		call(['tmux', 'set-option', '-gq', option, value])

	def _set_global_tmux_options(self):
		self._set_status_bar_colors()

	def _set_status_bar_colors(self):
		global_colors = self.colorscheme.global_colors
		for color_type in ('fg', 'bg'):
			if color_type in global_colors:
				cterm_color, hex_color = global_colors[color_type]
				self._set_tmux_option('status-{0}'.format(color_type),
									  'colour{0}'.format(cterm_color))

	def _add_get_cwd_to_segment_info(self, segment_info):
		varname = 'TMUX_PWD_' + segment_info['pane_id'].lstrip('%')
		if varname in segment_info['environ']:
			segment_info['getcwd'] = lambda: segment_info['environ'][varname]


renderer = TmuxRenderer
