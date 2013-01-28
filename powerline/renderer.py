# -*- coding: utf-8 -*-

from powerline.colorscheme import Colorscheme
from powerline.theme import Theme


class Renderer(object):
	ATTR_BOLD = 1
	ATTR_ITALIC = 2
	ATTR_UNDERLINE = 4

	TERM_24BIT_COLORS = False

	def __init__(self, theme_config, local_themes, theme_kwargs, term_24bit_colors=False):
		self.theme = Theme(theme_config=theme_config, **theme_kwargs)
		self.local_themes = local_themes
		self.theme_kwargs = theme_kwargs
		self.TERM_24BIT_COLORS = term_24bit_colors

	def add_local_theme(self, matcher, theme):
		if matcher in self.local_themes:
			raise KeyError('There is already a local theme with given matcher')
		self.local_themes[matcher] = theme

	def get_theme(self):
		for matcher in self.local_themes.keys():
			if matcher():
				match = self.local_themes[matcher]
				if 'config' in match:
					match['theme'] = Theme(theme_config=match.pop('config'), **self.theme_kwargs)
				return match['theme']
		else:
			return self.theme

	@staticmethod
	def _returned_value(rendered_highlighted, segments, output_raw):
		if output_raw:
			return rendered_highlighted, ''.join((segment['rendered_raw'] for segment in segments))
		else:
			return rendered_highlighted

	def render(self, mode=None, width=None, theme=None, segments=None, side=None, output_raw=False):
		'''Render all segments.

		When a width is provided, low-priority segments are dropped one at
		a time until the line is shorter than the width, or only segments
		with a negative priority are left. If one or more filler segments are
		provided they will fill the remaining space until the desired width is
		reached.
		'''
		theme = theme or self.get_theme()
		segments = segments or theme.get_segments(side)

		# Handle excluded/included segments for the current mode
		segments = [segment for segment in segments\
			if mode not in segment['exclude_modes'] or (segment['include_modes'] and segment in segment['include_modes'])]
		rendered_highlighted = self._render_segments(mode, theme, segments)
		if not width:
			# No width specified, so we don't need to crop or pad anything
			return self._returned_value(rendered_highlighted, segments, output_raw)

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

		return self._returned_value(self._render_segments(mode, theme, segments), segments, output_raw)

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
		try:
			mode = mode if mode in segments[0]['highlight'] else Colorscheme.DEFAULT_MODE_KEY
		except IndexError:
			return ''

		for index, segment in enumerate(segments):
			prev_segment = segments[index - 1] if index > 0 else theme.EMPTY_SEGMENT
			next_segment = segments[index + 1] if index < segments_len - 1 else theme.EMPTY_SEGMENT
			compare_segment = next_segment if segment['side'] == 'left' else prev_segment
			segment['rendered_raw'] = u''
			outer_padding = ' ' if (index == 0 and segment['side'] == 'left') or (index == segments_len - 1 and segment['side'] == 'right') else ''
			divider_type = 'soft' if compare_segment['highlight'][mode]['bg'] == segment['highlight'][mode]['bg'] else 'hard'

			divider_raw = theme.get_divider(segment['side'], divider_type)
			divider_highlighted = ''
			contents_raw = segment['contents']
			contents_highlighted = ''

			# Pad segments first
			if segment['type'] == 'filler':
				pass
			elif segment['draw_divider'] or divider_type == 'hard':
				if segment['side'] == 'left':
					contents_raw = outer_padding + contents_raw + ' '
					divider_raw = divider_raw + ' '
				else:
					contents_raw = ' ' + contents_raw + outer_padding
					divider_raw = ' ' + divider_raw
			elif contents_raw:
				if segment['side'] == 'left':
					contents_raw = outer_padding + contents_raw
				else:
					contents_raw = contents_raw + outer_padding
			else:
				raise ValueError('Unknown segment type')

			# Apply highlighting to padded dividers and contents
			if render_highlighted:
				if divider_type == 'soft' and segment['divider_highlight_group'] is not None:
					divider_highlighted = self.hl(divider_raw, segment['divider_highlight'][mode]['fg'], segment['divider_highlight'][mode]['bg'], False)
				elif divider_type == 'hard':
					divider_highlighted = self.hl(divider_raw, segment['highlight'][mode]['bg'], compare_segment['highlight'][mode]['bg'], False)
				contents_highlighted = self.hl(self.escape(contents_raw), **segment['highlight'][mode])

			# Append padded raw and highlighted segments to the rendered segment variables
			if segment['type'] == 'filler':
				rendered_highlighted += contents_highlighted if contents_raw else ''
			elif segment['draw_divider'] or divider_type == 'hard':
				# Draw divider if specified, or if it's a hard divider
				# Note: Hard dividers are always drawn, regardless of
				# the draw_divider option
				if segment['side'] == 'left':
					segment['rendered_raw'] += contents_raw + divider_raw
					rendered_highlighted += contents_highlighted + divider_highlighted
				else:
					segment['rendered_raw'] += divider_raw + contents_raw
					rendered_highlighted += divider_highlighted + contents_highlighted
			elif contents_raw:
				# Segments without divider
				if segment['side'] == 'left':
					segment['rendered_raw'] += contents_raw
					rendered_highlighted += contents_highlighted
				else:
					segment['rendered_raw'] += contents_raw
					rendered_highlighted += contents_highlighted
		rendered_highlighted += self.hl()
		return rendered_highlighted

	@staticmethod
	def _total_len(segments):
		'''Return total/rendered length of all segments.

		This method uses the rendered_raw property of the segments and requires
		that the segments have been rendered using the render() method first.
		'''
		return len(''.join([segment['rendered_raw'] for segment in segments]))

	@staticmethod
	def escape(string):
		return string

	@staticmethod
	def _int_to_rgb(int):
		r = (int >> 16) & 0xff
		g = (int >> 8) & 0xff
		b = int & 0xff
		return r, g, b

	def hl(self, contents=None, fg=None, bg=None, attr=None):
		raise NotImplementedError
