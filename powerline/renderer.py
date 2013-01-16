# -*- coding: utf-8 -*-

from colorscheme import Colorscheme
from theme import Theme


class Renderer(object):
	ATTR_BOLD = 1
	ATTR_ITALIC = 2
	ATTR_UNDERLINE = 4

	def __init__(self, theme_config, local_themes, theme_kwargs):
		self.theme = Theme(theme_config=theme_config, **theme_kwargs)
		self.local_themes = local_themes
		self.theme_kwargs = theme_kwargs

	def add_local_theme(self, matcher, theme):
		if matcher in self.local_themes:
			raise KeyError('There is already a local theme with given matcher')
		self.local_themes[matcher] = theme

	def get_theme(self):
		for matcher in self.local_themes.iterkeys():
			if matcher():
				match = self.local_themes[matcher]
				if 'config' in match:
					match['theme'] = Theme(theme_config=match.pop('config'), **self.theme_kwargs)
				return match['theme']
		else:
			return self.theme

	def render(self, mode, width=None, theme=None, segments=None):
		'''Render all segments.

		When a width is provided, low-priority segments are dropped one at
		a time until the line is shorter than the width, or only segments
		with a negative priority are left. If one or more filler segments are
		provided they will fill the remaining space until the desired width is
		reached.
		'''
		theme = theme or self.get_theme()
		segments = segments or theme.get_segments()

		# Handle excluded/included segments for the current mode
		segments = [segment for segment in segments\
			if mode not in segment['exclude_modes'] or (segment['include_modes'] and segment in segment['include_modes'])]
		rendered_highlighted = self._render_segments(mode, theme, segments)
		if not width:
			# No width specified, so we don't need to crop or pad anything
			return rendered_highlighted

		# Create an ordered list of segments that can be dropped
		segments_priority = [segment for segment in sorted(segments, key=lambda segment: segment['priority'], reverse=True) if segment['priority'] > 0]
		while self._total_len(segments) > width and len(segments_priority):
			segments.remove(segments_priority[0])
			segments_priority.pop(0)

		# Do another render pass so we can calculate the correct amount of filler space
		self._render_segments(mode, theme, segments, render_highlighted=False)

		# Distribute the remaining space on the filler segments
		segments_fillers = [segment for segment in segments if segment['type'] == 'filler']
		if segments_fillers:
			segments_fillers_len, segments_fillers_remainder = divmod((width - self._total_len(segments)), len(segments_fillers))
			segments_fillers_contents = ' ' * segments_fillers_len
			for segment in segments_fillers:
				segment['contents'] = segments_fillers_contents
			# Add remainder whitespace to the first filler segment
			segments_fillers[0]['contents'] += ' ' * segments_fillers_remainder
		return self._render_segments(mode, theme, segments)

	def _render_segments(self, mode, theme, segments, render_highlighted=True):
		'''Internal segment rendering method.

		This method loops through the segment array and compares the
		foreground/background colors and divider properties and returns the
		rendered statusline as a string.

		The method always renders the raw segment contents (i.e. without
		highlighting strings added), and only renders the highlighted
		statusline if render_highlighted is True.
		'''
		rendered_highlighted = u''
		segments_len = len(segments)
		mode = mode if mode in segments[0]['highlight'] else Colorscheme.DEFAULT_MODE_KEY

		for index, segment in enumerate(segments):
			prev_segment = segments[index - 1] if index > 0 else theme.EMPTY_SEGMENT
			next_segment = segments[index + 1] if index < segments_len - 1 else theme.EMPTY_SEGMENT
			compare_segment = next_segment if segment['side'] == 'left' else prev_segment
			segment['rendered_raw'] = u''
			outer_padding = ' ' if index == 0 or (index == segments_len - 1 and segment['side'] == 'right') else ''
			divider_type = 'soft' if compare_segment['highlight'][mode]['bg'] == segment['highlight'][mode]['bg'] else 'hard'
			divider = theme.get_divider(segment['side'], divider_type)
			divider_hl = ''
			segment_hl = ''

			if render_highlighted:
				if divider_type == 'hard':
					divider_hl = self.hl(segment['highlight'][mode]['bg'], compare_segment['highlight'][mode]['bg'], False)
				segment_hl = self.hl(**segment['highlight'][mode])

			if segment['type'] == 'filler':
				rendered_highlighted += segment['contents'] or ''
			elif segment['draw_divider'] or divider_type == 'hard':
				# Draw divider if specified, or if it's a hard divider
				# Note: Hard dividers are always drawn, regardless of
				# the draw_divider option
				if segment['side'] == 'left':
					segment['rendered_raw'] += outer_padding + segment['contents'] + ' ' + divider + ' '
					rendered_highlighted += segment_hl + outer_padding + segment['contents'] + ' ' + divider_hl + divider + ' '
				else:
					segment['rendered_raw'] += ' ' + divider + ' ' + segment['contents'] + outer_padding
					rendered_highlighted += ' ' + divider_hl + divider + segment_hl + ' ' + segment['contents'] + outer_padding
			elif segment['contents']:
				# Segments without divider
				if segment['side'] == 'left':
					segment['rendered_raw'] += outer_padding + segment['contents']
					rendered_highlighted += segment_hl + outer_padding + segment['contents']
				else:
					segment['rendered_raw'] += segment['contents'] + outer_padding
					rendered_highlighted += segment_hl + segment['contents'] + outer_padding
			else:
				raise ValueError('Unknown segment type')
		return rendered_highlighted

	def _total_len(self, segments):
		'''Return total/rendered length of all segments.

		This method uses the rendered_raw property of the segments and requires
		that the segments have been rendered using the render() method first.
		'''
		return len(''.join([segment['rendered_raw'] for segment in segments]))

	def hl(self, fg=None, bg=None, attr=None):
		raise NotImplementedError
