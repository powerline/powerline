# -*- coding: utf-8 -*-

from lib.colors import cterm_to_hex


class Powerline(object):
	ATTR_BOLD = 1
	ATTR_ITALIC = 2
	ATTR_UNDERLINE = 4

	dividers = {
		'l': {
			'hard': u'⮀',
			'soft': u'⮁',
		},
		'r': {
			'hard': u'⮂',
			'soft': u'⮃',
		},
	}

	def __init__(self, segments):
		'''Create a new Powerline.

		Segments that have empty contents and aren't filler segments are
		dropped from the segment array.
		'''
		self.segments = [segment for segment in segments if segment['contents'] or segment['filler']]
		self._hl = {}

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
		def render_segments(segments, render_highlighted=True):
			'''Render a segment array.

			By default this function renders both raw (un-highlighted segments
			used for calculating final width) and highlighted segments. The raw
			rendering is used for calculating the total width for dropping
			low-priority segments.
			'''
			rendered_highlighted = u''
			segments_len = len(segments)
			empty_segment = mksegment()

			for idx, segment in enumerate(segments):
				prev = segments[idx - 1] if idx > 0 else empty_segment
				next = segments[idx + 1] if idx < segments_len - 1 else empty_segment

				compare = next if segment['side'] == 'l' else prev
				outer_padding = ' ' if idx == 0 or idx == segments_len - 1 else ''
				divider_type = 'soft' if compare['bg'] == segment['bg'] else 'hard'
				divider = self.dividers[segment['side']][divider_type]
				divider_hl = ''
				segment_hl = ''

				if render_highlighted:
					# Generate and cache renderer highlighting
					if divider_type == 'hard':
						hl_key = (segment['bg'], compare['bg'])
						if not hl_key in self._hl:
							self._hl[hl_key] = renderer.hl(*hl_key)
						divider_hl = self._hl[hl_key]

					hl_key = (segment['fg'], segment['bg'], segment['attr'])
					if not hl_key in self._hl:
						self._hl[hl_key] = renderer.hl(*hl_key)
					segment_hl = self._hl[hl_key]

				if segment['filler']:
					# Filler segments shouldn't be padded
					rendered_highlighted += segment['contents']
				elif segment['draw_divider'] and (divider_type == 'hard' or segment['side'] == compare['side']):
					# Draw divider if specified, and if the next segment is on
					# the opposite side only draw the divider if it's a hard
					# divider
					if segment['side'] == 'l':
						segment['rendered_raw'] += outer_padding + segment['contents'] + ' ' + divider + ' '
						rendered_highlighted += segment_hl + outer_padding + segment['contents'] + ' ' + divider_hl + divider + ' '
					else:
						segment['rendered_raw'] += ' ' + divider + ' ' + segment['contents'] + outer_padding
						rendered_highlighted += ' ' + divider_hl + divider + segment_hl + ' ' + segment['contents'] + outer_padding
				elif segment['contents']:
					# Segments without divider
					if segment['side'] == 'l':
						segment['rendered_raw'] += outer_padding + segment['contents']
						rendered_highlighted += segment_hl + outer_padding + segment['contents']
					else:
						segment['rendered_raw'] += segment['contents'] + outer_padding
						rendered_highlighted += segment_hl + segment['contents'] + outer_padding
				else:
					# Unknown segment type, skip it
					continue

			return rendered_highlighted

		rendered_highlighted = render_segments(self.segments)

		if not width:
			# No width specified, so we don't need to crop or pad anything
			return rendered_highlighted

		# Create an ordered list of segments that can be dropped
		segments_priority = [segment for segment in sorted(self.segments, key=lambda segment: segment['priority'], reverse=True) if segment['priority'] > 0]

		while self._total_len() > width and len(segments_priority):
			self.segments.remove(segments_priority[0])
			segments_priority.pop(0)

		# Distribute the remaining space on the filler segments
		segments_fillers = [segment for segment in self.segments if segment['filler'] is True]
		if segments_fillers:
			segments_fillers_len, segments_fillers_remainder = divmod((width - self._total_len()), len(segments_fillers))
			segments_fillers_contents = ' ' * segments_fillers_len
			for segment in segments_fillers:
				segment['contents'] = segments_fillers_contents
			# Add remainder whitespace to the first filler segment
			segments_fillers[0]['contents'] += ' ' * segments_fillers_remainder

		return render_segments(self.segments)

	def _total_len(self):
		'''Return total/rendered length of all segments.

		This method uses the rendered_raw property of the segments and requires
		that the segments have been rendered using the render() method first.
		'''
		return len(''.join([segment['rendered_raw'] for segment in self.segments]))


def mksegment(contents=None, cterm_fg=False, cterm_bg=False, attr=False, hex_fg=False, hex_bg=False, side='l', draw_divider=True, priority=-1, filler=False):
	'''Convenience wrapper for segment generation.
	'''
	try:
		contents = unicode(contents or u'')
	except UnicodeDecodeError:
		contents = contents.decode('utf-8') or u''

	return {
		'contents': contents,
		'fg': (cterm_fg, hex_fg or cterm_to_hex.get(cterm_fg, 0xffffff)),
		'bg': (cterm_bg, hex_bg or cterm_to_hex.get(cterm_bg, 0x000000)),
		'attr': attr,
		'side': side,
		'draw_divider': False if filler else draw_divider,
		'priority': priority,
		'filler': filler,
		'rendered_raw': u'',
	}
