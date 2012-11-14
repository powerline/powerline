class Segment:
	'''Powerline segment renderer.

	Powerline segments are initially structured as a tree of segments and sub
	segments. This is to give the segments a sense of grouping and "scope", to
	avoid having to define all the properties (fg, bg, etc.) for every single
	segment. By grouping you can e.g. provide a common background color for
	several segments.

	Usage example:

		from lib.core import Segment
		from lib.renderers import TerminalSegmentRenderer

		powerline = Segment([
			Segment('First segment'),
			Segment([
				Segment('Grouped segment 1'),
				Segment('Grouped segment 2'),
			]),
		])

		print(powerline.render(TerminalSegmentRenderer))
	'''
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

	ATTR_BOLD = 1
	ATTR_ITALIC = 2
	ATTR_UNDERLINE = 4

	def __init__(self, contents=None, fg=None, bg=None, attr=None, side=None, padding=None, draw_divider=None, priority=None, filler=None):
		'''Create a new Powerline segment.
		'''
		self.parent = None

		self.contents = contents or ''
		self.fg = fg
		self.bg = bg
		self.attr = attr
		self.side = side
		self.padding = padding
		self.draw_divider = draw_divider
		self.priority = priority
		self.filler = filler

		if self.filler:
			# Filler segments should never have any dividers
			self.draw_divider = False

		# Set the parent property for child segments
		for segment in self.contents:
			try:
				segment.parent = self
			except AttributeError:
				# Not a Segment node
				continue

	def init_attributes(self):
		'''Initialize the default attributes for this segment.

		This method is intended to be run when all segments in the segment tree
		have the correct parent segment set (i.e. after the root segment has
		been instantiated).
		'''
		def lookup_attr(attr, default, obj=self):
			'''Looks up attributes in the segment tree.

			If the attribute isn't found anywhere, the default argument is used
			for this segment.
			'''
			# Check if the current object has the attribute defined
			obj_attr = getattr(obj, attr)
			if obj_attr is None:
				try:
					# Check if the object's parent has the attribute defined
					return lookup_attr(attr, default, obj.parent)
				except AttributeError:
					# Root node reached
					return default
			return obj_attr

		# Set default attributes
		self.fg = lookup_attr('fg', False)
		self.bg = lookup_attr('bg', False)
		self.attr = lookup_attr('attr', False)
		self.side = lookup_attr('side', 'l')
		self.padding = lookup_attr('padding', ' ')
		self.draw_divider = lookup_attr('draw_divider', True)
		self.priority = lookup_attr('priority', -1)
		self.filler = lookup_attr('filler', False)

		try:
			if len(self.fg) == 2:
				self.fg = self.fg
		except TypeError:
			# Only the terminal color is defined, so we need to get the hex color
			from lib.colors import cterm_to_hex
			self.fg = [self.fg, cterm_to_hex(self.fg)]

		try:
			if len(self.bg) == 2:
				self.bg = self.bg
		except TypeError:
			# Only the terminal color is defined, so we need to get the hex color
			from lib.colors import cterm_to_hex
			self.bg = [self.bg, cterm_to_hex(self.bg)]

	def render(self, renderer, width=None):
		'''Render the segment and all child segments.

		This method flattens the segment and all its child segments into
		a one-dimensional array. It then loops through this array and compares
		the foreground/background colors and divider/padding properties and
		returns the rendered statusline as a string.

		When a width is provided, low-priority segments are dropped one at
		a time until the line is shorter than the width, or only segments
		with a negative priority are left. If one or more filler segments are
		provided they will fill the remaining space until the desired width is
		reached.
		'''
		def flatten(segment):
			'''Flatten the segment tree into a one-dimensional array.
			'''
			ret = []
			for child_segment in segment.contents:
				if isinstance(child_segment.contents, str):
					# If the contents of the child segment is a string then
					# this is a tree node
					child_segment.init_attributes()
					ret.append(child_segment)
				else:
					# This is a segment group that should be flattened
					ret += flatten(child_segment)
			return ret

		segments = flatten(self)

		def render_segments(segments, render_raw=True, render_highlighted=True):
			'''Render a one-dimensional segment array.

			By default this function renders both raw (un-highlighted segments
			used for calculating final width) and highlighted segments.
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
						segment_format = '{segment_hl}{padding}{contents}{padding}{divider_hl}{divider}'
					else:
						segment_format = '{divider_hl}{divider}{segment_hl}{padding}{contents}{padding}'
				elif segment.contents:
					# Soft divided segments
					segment_format = '{segment_hl}{padding}{contents}{padding}'
				else:
					# Unknown segment type, skip it
					continue

				if render_raw is True and segment.filler is False:
					# Filler segments must be empty when used e.g. in vim (the
					# %=%< segment which disappears), so they will be skipped
					# when calculating the width using the raw rendering
					rendered_raw += segment_format.format(
						padding=segment.padding,
						divider=divider,
						contents=segment.contents,
						divider_hl='',
						segment_hl='',
					)

				if render_highlighted is True:
					rendered_highlighted += segment_format.format(
						padding=segment.padding,
						divider=divider,
						contents=segment.contents,
						divider_hl='' if divider_type == 'soft' else renderer.hl(segment.bg, compare_segment.bg),
						segment_hl=renderer.hl(segment.fg, segment.bg, segment.attr),
					)

			return {
				'highlighted': rendered_highlighted,
				'raw': rendered_raw,
			}

		rendered = render_segments(segments)

		if not width:
			# No width specified, so we don't need to crop or pad anything
			return rendered['highlighted']

		# Create an ordered list of segments that can be dropped
		segments_priority = [segment for segment in sorted(segments, key=lambda segment: segment.priority, reverse=True) if segment.priority > 0]

		while len(rendered['raw']) > width and len(segments_priority):
			segments.remove(segments_priority[0])
			segments_priority.pop(0)

			rendered = render_segments(segments, render_highlighted=False)

		# Distribute the remaining space on the filler segments
		segments_fillers = [segment for segment in segments if segment.filler is True]
		if segments_fillers:
			segments_fillers_contents = ' ' * int((width - len(rendered['raw'])) / len(segments_fillers))
			for segment in segments_fillers:
				segment.contents = segments_fillers_contents

		# Do a final render now that we have handled the cropping and padding
		rendered = render_segments(segments, render_raw=False)

		return rendered['highlighted']
