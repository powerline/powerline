# vim:fileencoding=utf-8:noet
from __future__ import absolute_import, unicode_literals
from subprocess import call

from powerline.renderer import Renderer
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


class TmuxRenderer(Renderer):
	'''Powerline tmux segment renderer.'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('#')] = '##[]'

	default_window_status_left_segment = {
	    'name': 'window_status_left',
	    'type': 'string',
	    'contents': '#I',
	}

	default_window_status_right_segment = {
	    'name': 'window_status_right',
	    'type': 'string',
	    'contents': '#W',
	}

	default_current_window_status_left_segment = {
	    'name': 'current_window_status_left',
	    'type': 'string',
	    'contents': '#I',
	}

	default_current_window_status_right_segment = {
	    'name': 'current_window_status_right',
	    'type': 'string',
	    'contents': '#W',
	}

	transition_segment = {
		'name': 'global',
		'type': 'string',
		'contents': ''
	}

	_default_window_status_segments = (
		default_window_status_left_segment,
		default_window_status_right_segment,
		default_current_window_status_left_segment,
		default_current_window_status_right_segment,
		transition_segment
	)

	@property
	def default_window_status_segments(self):
		return [self.theme.get_segment(segment, 'left')
				for segment in self._default_window_status_segments]

	def __init__(self, *args, **kwargs):
		super(TmuxRenderer, self).__init__(*args, **kwargs)
		self.theme.set_default_segments('misc', self.default_window_status_segments)

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
		self._set_status_formats()

	def _set_status_bar_colors(self):
		global_colors = self.colorscheme.global_colors
		for color_type in ('fg', 'bg'):
			if color_type in global_colors:
				cterm_color, hex_color = global_colors[color_type]
				self._set_tmux_option('status-{0}'.format(color_type),
									  'colour{0}'.format(cterm_color))

	def _set_status_formats(self):
		# This is super gross, but we are basically trying to emulate the flow.
		segment_name_to_segment = dict(
			(segment['name'], segment)
			for segment in self.theme.get_segments(side='misc')
		)
		dummy_leftmost_segment = segment_name_to_segment['global'].copy()
		self._set_tmux_option(
			"window-status-format",
			self._render_tmux_status_segments(
				segment_name_to_segment['window_status_left'].copy(),
				segment_name_to_segment['window_status_right'].copy(),
				segment_name_to_segment['window_status_left'].copy(),
				dummy_leftmost_segment.copy()
			)
		)
		self._set_tmux_option(
			"window-status-current-format",
			self._render_tmux_status_segments(
				segment_name_to_segment['current_window_status_left'].copy(),
				segment_name_to_segment['current_window_status_right'].copy(),
				segment_name_to_segment['window_status_left'].copy(),
				dummy_leftmost_segment
			)
		)

	def _render_tmux_status_segments(self, left_status_segment, right_status_segment, right_compare_segment, dummy_leftmost_segment):
		right_compare_segment = self._get_highlighting(right_compare_segment, None)
		dummy_leftmost_segment = self._get_highlighting(dummy_leftmost_segment, None)
		left_status_segment = self._get_highlighting(left_status_segment, None)
		right_status_segment = self._get_highlighting(right_status_segment, None)
		dummy_leftmost_segment = self._render_segment(
			self.theme,
			dummy_leftmost_segment,
			compare_segment=left_status_segment,
			outer_padding='',
			render_highlighted=True,
			translate_characters=False,
			divider_type='hard'
		)
		left_status_segment = self._render_segment(
			self.theme,
			left_status_segment,
			compare_segment=right_status_segment,
			outer_padding='',
			render_highlighted=True,
			translate_characters=False,
		)
		right_status_segment = self._render_segment(
			self.theme,
			right_status_segment,
			compare_segment=right_compare_segment, # These are going to loop
			outer_padding='',
			render_highlighted=True,
			translate_characters=False
		)
		return ''.join(segment['_rendered_hl'] for segment in
				(dummy_leftmost_segment, left_status_segment, right_status_segment))

	def _add_get_cwd_to_segment_info(self, segment_info):
		varname = 'TMUX_PWD_' + segment_info['pane_id'].lstrip('%')
		if varname in segment_info['environ']:
			segment_info['getcwd'] = lambda: segment_info['environ'][varname]


renderer = TmuxRenderer
