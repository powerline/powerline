# -*- coding: utf-8 -*-

from powerline.colorscheme import DEFAULT_MODE_KEY
from powerline.theme import Theme


class Renderer(object):
	def __init__(self, theme_config, local_themes, theme_kwargs, **options):
		self.__dict__.update(options)
		self.theme = Theme(theme_config=theme_config, **theme_kwargs)
		self.local_themes = local_themes
		self.theme_kwargs = theme_kwargs

	def add_local_theme(self, matcher, theme):
		if matcher in self.local_themes:
			raise KeyError('There is already a local theme with given matcher')
		self.local_themes[matcher] = theme

	def get_theme(self, matcher_info):
		for matcher in self.local_themes.keys():
			if matcher(matcher_info):
				match = self.local_themes[matcher]
				if 'config' in match:
					match['theme'] = Theme(theme_config=match.pop('config'), **self.theme_kwargs)
				return match['theme']
		else:
			return self.theme

	def render(self, mode=None, width=None, side=None, output_raw=False, segment_info=None, matcher_info=None):
		'''Render all segments.

		When a width is provided, low-priority segments are dropped one at
		a time until the line is shorter than the width, or only segments
		with a negative priority are left. If one or more filler segments are
		provided they will fill the remaining space until the desired width is
		reached.
		'''
		theme = self.get_theme(matcher_info)
		segments = theme.get_segments(side)

		if segment_info:
			theme.segment_info.update(segment_info)

		# Handle excluded/included segments for the current mode
		segments = [segment for segment in segments\
			if mode not in segment['exclude_modes'] or (segment['include_modes'] and segment in segment['include_modes'])]

		segments = [segment for segment in self._render_segments(mode, theme, segments)]

		if not width:
			# No width specified, so we don't need to crop or pad anything
			return self._returned_value(u''.join([segment['_rendered_hl'] for segment in segments]) + self.hlstyle(), segments, output_raw)

		# Create an ordered list of segments that can be dropped
		segments_priority = [segment for segment in sorted(segments, key=lambda segment: segment['priority'], reverse=True) if segment['priority'] > 0]
		while sum([segment['_len'] for segment in segments]) > width and len(segments_priority):
			segments.remove(segments_priority[0])
			segments_priority.pop(0)

		# Distribute the remaining space on spacer segments
		segments_spacers = [segment for segment in segments if segment['width'] == 'auto']
		if segments_spacers:
			distribute_len, distribute_len_remainder = divmod(width - sum([segment['_len'] for segment in segments]), len(segments_spacers))
			for segment in segments_spacers:
				if segment['align'] == 'l':
					segment['_space_right'] += distribute_len
				elif segment['align'] == 'r':
					segment['_space_left'] += distribute_len
				elif segment['align'] == 'c':
					space_side, space_side_remainder = divmod(distribute_len, 2)
					segment['_space_left'] += space_side + space_side_remainder
					segment['_space_right'] += space_side
			segments_spacers[0]['_space_right'] += distribute_len_remainder

		rendered_highlighted = u''.join([segment['_rendered_hl'] for segment in self._render_segments(mode, theme, segments)]) + self.hlstyle()

		return self._returned_value(rendered_highlighted, segments, output_raw)

	def _render_segments(self, mode, theme, segments, render_highlighted=True):
		'''Internal segment rendering method.

		This method loops through the segment array and compares the
		foreground/background colors and divider properties and returns the
		rendered statusline as a string.

		The method always renders the raw segment contents (i.e. without
		highlighting strings added), and only renders the highlighted
		statusline if render_highlighted is True.
		'''
		segments_len = len(segments)
		try:
			mode = mode if mode in segments[0]['highlight'] else DEFAULT_MODE_KEY
		except IndexError:
			pass

		for index, segment in enumerate(segments):
			segment['_rendered_raw'] = u''
			segment['_rendered_hl'] = u''

			prev_segment = segments[index - 1] if index > 0 else theme.EMPTY_SEGMENT
			next_segment = segments[index + 1] if index < segments_len - 1 else theme.EMPTY_SEGMENT
			compare_segment = next_segment if segment['side'] == 'left' else prev_segment
			outer_padding = ' ' if (index == 0 and segment['side'] == 'left') or (index == segments_len - 1 and segment['side'] == 'right') else ''
			divider_type = 'soft' if compare_segment['highlight'][mode]['bg'] == segment['highlight'][mode]['bg'] else 'hard'

			divider_raw = theme.get_divider(segment['side'], divider_type)
			divider_spaces = theme.get_spaces()
			divider_highlighted = ''
			contents_raw = segment['contents']
			contents_highlighted = ''

			# Pad segments first
			if segment['draw_divider'] or (divider_type == 'hard' and segment['width'] != 'auto'):
				if segment['side'] == 'left':
					contents_raw = outer_padding + (segment['_space_left'] * ' ') + contents_raw + ((divider_spaces + segment['_space_right']) * ' ')
				else:
					contents_raw = ((divider_spaces + segment['_space_left']) * ' ') + contents_raw + (segment['_space_right'] * ' ') + outer_padding
			else:
				if segment['side'] == 'left':
					contents_raw = outer_padding + (segment['_space_left'] * ' ') + contents_raw + (segment['_space_right'] * ' ')
				else:
					contents_raw = (segment['_space_left'] * ' ') + contents_raw + (segment['_space_right'] * ' ') + outer_padding

			# Replace spaces with no-break spaces
			contents_raw = contents_raw.replace(' ', u'\u00a0')
			divider_raw = divider_raw.replace(' ', u'\u00a0')

			# Apply highlighting to padded dividers and contents
			if render_highlighted:
				if divider_type == 'soft':
					divider_highlight_group_key = 'highlight' if segment['divider_highlight_group'] is None else 'divider_highlight'
					divider_fg = segment[divider_highlight_group_key][mode]['fg']
					divider_bg = segment[divider_highlight_group_key][mode]['bg']
				else:
					divider_fg = segment['highlight'][mode]['bg']
					divider_bg = compare_segment['highlight'][mode]['bg']
				divider_highlighted = self.hl(divider_raw, divider_fg, divider_bg, False)
				contents_highlighted = self.hl(self.escape(contents_raw), **segment['highlight'][mode])

			# Append padded raw and highlighted segments to the rendered segment variables
			if segment['draw_divider'] or (divider_type == 'hard' and segment['width'] != 'auto'):
				if segment['side'] == 'left':
					segment['_rendered_raw'] += contents_raw + divider_raw
					segment['_rendered_hl'] += contents_highlighted + divider_highlighted
				else:
					segment['_rendered_raw'] += divider_raw + contents_raw
					segment['_rendered_hl'] += divider_highlighted + contents_highlighted
			else:
				if segment['side'] == 'left':
					segment['_rendered_raw'] += contents_raw
					segment['_rendered_hl'] += contents_highlighted
				else:
					segment['_rendered_raw'] += contents_raw
					segment['_rendered_hl'] += contents_highlighted
			segment['_len'] = len(segment['_rendered_raw'])
			yield segment

	@staticmethod
	def _returned_value(rendered_highlighted, segments, output_raw):
		if output_raw:
			return rendered_highlighted, ''.join((segment['_rendered_raw'] for segment in segments))
		else:
			return rendered_highlighted

	@staticmethod
	def escape(string):
		return string

	@staticmethod
	def _int_to_rgb(int):
		r = (int >> 16) & 0xff
		g = (int >> 8) & 0xff
		b = int & 0xff
		return r, g, b

	def hlstyle(fg=None, bg=None, attr=None):
		raise NotImplementedError

	def hl(self, contents, fg=None, bg=None, attr=None):
		return self.hlstyle(fg, bg, attr) + (contents or u'')
