# -*- coding: utf-8 -*-


class Powerline:
	dividers = {
		'l': {
			'hard': '⮀',
			'soft': '⮁',
		},
		'r': {
			'hard': '⮂',
			'soft': '⮃',
		},
	}

	def __init__(self, segments):
		'''Create a new Powerline.

		Segments that have empty contents and aren't filler segments are
		dropped from the segment array.
		'''
		self.segments = [segment for segment in segments if segment.contents or segment.filler]

	def render(self, renderer, width=None):
		'''Render all the segments with the specified renderer.

		This method loops through the segment array and compares the
		foreground/background colors and divider properties and returns the
		rendered statusline as a string.

		When a width is provided, low-priority segments are dropped one at
		a time until the line is shorter than the width, or only segments
		with a negative priority are left. If one or more filler segments are
		provided they will fill the remaining space until the desired width is
		reached.
		'''
		def render_segments(segments, render_raw=True, render_highlighted=True):
			'''Render a segment array.

			By default this function renders both raw (un-highlighted segments
			used for calculating final width) and highlighted segments. The raw
			rendering is used for calculating the total width for dropping
			low-priority segments.
			'''
			rendered_raw = ''
			rendered_highlighted = ''

			for idx, segment in enumerate(segments):
				prev = segments[idx - 1] if idx > 0 else Segment()
				next = segments[idx + 1] if idx < len(segments) - 1 else Segment()

				compare_segment = next if segment.side == 'l' else prev
				divider_type = 'soft' if compare_segment.bg == segment.bg else 'hard'
				divider = self.dividers[segment.side][divider_type]

				if segment.filler:
					# Filler segments shouldn't be padded
					segment_format = '{contents}'
				elif segment.draw_divider and (divider_type == 'hard' or segment.side == compare_segment.side):
					# Draw divider if specified, and if the next segment is on
					# the opposite side only draw the divider if it's a hard
					# divider
					if segment.side == 'l':
						segment_format = '{segment_hl}{outer_padding}{contents} {divider_hl}{divider} '
					else:
						segment_format = ' {divider_hl}{divider}{segment_hl} {contents}{outer_padding}'
				elif segment.contents:
					# Segments without divider
					segment_format = '{segment_hl}{contents}{outer_padding}'
				else:
					# Unknown segment type, skip it
					continue

				if render_raw is True and segment.filler is False:
					# Filler segments must be empty when used e.g. in vim (the
					# %=%< segment which disappears), so they will be skipped
					# when calculating the width using the raw rendering
					rendered_raw += segment_format.format(
						divider=divider,
						contents=segment.contents,
						divider_hl='',
						segment_hl='',
						outer_padding=' ' if idx == 0 or idx == len(segments) - 1 else '',
					)

				if render_highlighted is True:
					rendered_highlighted += segment_format.format(
						divider=divider,
						contents=segment.contents,
						divider_hl='' if divider_type == 'soft' else renderer.hl(segment.bg, compare_segment.bg),
						segment_hl=renderer.hl(segment.fg, segment.bg, segment.attr),
						outer_padding=' ' if idx == 0 or idx == len(segments) - 1 else '',
					)

			return {
				'highlighted': rendered_highlighted.decode('utf-8'),
				'raw': rendered_raw.decode('utf-8'),
			}

		rendered = render_segments(self.segments)

		if not width:
			# No width specified, so we don't need to crop or pad anything
			return rendered['highlighted']

		# Create an ordered list of segments that can be dropped
		segments_priority = [segment for segment in sorted(self.segments, key=lambda segment: segment.priority, reverse=True) if segment.priority > 0]

		while len(rendered['raw']) > width and len(segments_priority):
			self.segments.remove(segments_priority[0])
			segments_priority.pop(0)

			rendered = render_segments(self.segments, render_highlighted=False)

		# Distribute the remaining space on the filler segments
		segments_fillers = [segment for segment in self.segments if segment.filler is True]
		if segments_fillers:
			segments_fillers_contents = ' ' * int((width - len(rendered['raw'])) / len(segments_fillers))
			for segment in segments_fillers:
				segment.contents = segments_fillers_contents

		# Do a final render now that we have handled the cropping and padding
		rendered = render_segments(self.segments, render_raw=False)

		return rendered['highlighted']


class Segment:
	ATTR_BOLD = 1
	ATTR_ITALIC = 2
	ATTR_UNDERLINE = 4

	def __init__(self, contents=None, fg=False, bg=False, attr=False, side='l', draw_divider=True, priority=-1, filler=False):
		'''Create a new Powerline segment.
		'''
		self.contents = str(contents or '')
		self.fg = fg
		self.bg = bg
		self.attr = attr
		self.side = side
		self.draw_divider = draw_divider
		self.priority = priority
		self.filler = filler

		if self.filler:
			# Filler segments should never have any dividers
			self.draw_divider = False

		try:
			if len(self.fg) != 2:
				raise TypeError
		except TypeError:
			# Only the terminal color is defined, so we need to get the hex color
			from lib.colors import cterm_to_hex
			self.fg = [self.fg, cterm_to_hex(self.fg)]

		try:
			if len(self.bg) != 2:
				raise TypeError
		except TypeError:
			# Only the terminal color is defined, so we need to get the hex color
			from lib.colors import cterm_to_hex
			self.bg = [self.bg, cterm_to_hex(self.bg)]
