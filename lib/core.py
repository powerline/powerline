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
	separators = {
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

	def __init__(self, content='', fg=None, bg=None, attr=None, side=None, padding=None, separate=None):
		'''Create a new segment.

		No arguments are required when creating new segments, as
		empty/colorless segments can be used e.g.  as left/right separators.
		'''
		self.content = content
		self.parent = None
		self.prev = None
		self.next = None

		try:
			if len(fg) == 2:
				self._fg = fg
		except TypeError:
			# Only the terminal color is defined, so we need to get the hex color
			from lib.colors import cterm_to_hex
			self._fg = [fg, cterm_to_hex(fg)]

		try:
			if len(bg) == 2:
				self._bg = bg
		except TypeError:
			# Only the terminal color is defined, so we need to get the hex color
			from lib.colors import cterm_to_hex
			self._bg = [bg, cterm_to_hex(bg)]

		self._attr = attr
		self._side = side
		self._padding = padding
		self._separate = separate

	@property
	def fg(self):
		'''Segment foreground color property.

		Recursively searches for the property or the parent segments' property
		until one is found. If this property is not defined anywhere in the
		tree, the default foreground color is used.
		'''
		if self.parent and self._fg[0] is None:
			return self.parent.fg
		return self._fg if self._fg[0] is not None else False

	@property
	def bg(self):
		'''Segment background color property.

		Recursively searches for the property or the parent segments' property
		until one is found. If this property is not defined anywhere in the
		tree, the default background color is used.
		'''
		if self.parent and self._bg[0] is None:
			return self.parent.bg
		return self._bg if self._bg[0] is not None else False

	@property
	def attr(self):
		'''Segment attribute property.

		Recursively searches for the property or the parent segments' property
		until one is found. If this property is not defined anywhere in the
		tree, no attributes are applied.
		'''
		if self.parent and self._attr is None:
			return self.parent.attr
		return self._attr if self._attr is not None else 0

	@property
	def side(self):
		'''Segment side property.

		Recursively searches for the property or the parent segments' property
		until one is found. If this property is not defined anywhere in the
		tree, the left side is used for all segments.
		'''
		if self.parent and self._side is None:
			return self.parent.side
		return self._side if self._side is not None else 'l'

	@property
	def padding(self):
		'''Segment padding property.

		Return which string is used to pad the segment before and after the
		separator symbol.

		Recursively searches for the property or the parent segments' property
		until one is found. If this property is not defined anywhere in the
		tree, a single space is used for padding.
		'''
		if self.parent and self._padding is None:
			return self.parent.padding
		return self._padding if self._padding is not None else ' '

	@property
	def separate(self):
		'''Segment separation property.

		Returns whether a separator symbol should be drawn before/after the
		segment.

		Recursively searches for the property or the parent segments' property
		until one is found. If this property is not defined anywhere in the
		tree, then separators will be drawn around all segments.
		'''
		if self.parent and self._separate is None:
			return self.parent.separate
		return self._separate if self._separate is not None else True

	@property
	def separator(self):
		'''Segment separator property.

		Returns the separator symbol to be used, depending on which side this
		segment is on.
		'''
		return self.separators[self.side]

	def render(self, renderer):
		'''Render the segment and all child segments.

		This method flattens the segment and all its child segments into
		a one-dimensional array. It then loops through this array and compares
		the foreground/background colors and separator/padding properties and
		returns the rendered statusline as a string.
		'''
		def flatten(segment):
			'''Flattens the segment tree into a one-dimensional array.
			'''
			ret = []
			for child_segment in segment.content:
				child_segment.parent = segment
				if isinstance(child_segment.content, str):
					# If the contents of the child segment is a string then
					# this is a tree node
					ret.append(child_segment)
				else:
					# This is a segment group that should be flattened
					ret += flatten(child_segment)
			return ret

		segments = flatten(self)
		output = ''

		# Loop through the segment array and create the segments, colors and
		# separators
		#
		# TODO Make this prettier
		for idx, segment in enumerate(segments):
			# Ensure that we always have a previous/next segment, if we're at
			# the beginning/end of the array an empty segment is used for the
			# prev/next segment
			segment.prev = segments[idx - 1] if idx > 0 else Segment()
			segment.next = segments[idx + 1] if idx < len(segments) - 1 else Segment()

			if segment.side == 'l':
				output += renderer.hl(segment.fg, segment.bg, segment.attr)
				output += segment.padding
				output += segment.content
				output += renderer.hl(attr=False)
				if segment.content:
					if segment.next.bg == segment.bg:
						if segment.next.content and segment.separate:
							output += segment.padding
							if segment.next.side == segment.side:
								# Only draw the soft separator if this segment is on the same side
								# No need to draw the soft separator if there's e.g. a vim divider in the next segment
								output += segment.separator['soft']
					# Don't draw a hard separator if the next segment is on
					# the opposite side, it screws up the coloring
					elif segment.next.side == segment.side:
						output += segment.padding
						output += renderer.hl(segment.bg, segment.next.bg)
						output += segment.separator['hard']
			else:
				pad_pre = False
				if segment.content:
					if segment.prev.bg == segment.bg:
						if segment.prev.content and segment.separate:
							pad_pre = True
							if segment.prev.side == segment.side:
								# Only draw the soft separator if this segment is on the same side
								# No need to draw the soft separator if there's e.g. a vim divider in the previous segment
								output += segment.separator['soft']
					else:
						pad_pre = True
						output += renderer.hl(segment.bg, segment.prev.bg)
						output += segment.separator['hard']
				output += renderer.hl(segment.fg, segment.bg, segment.attr)
				if pad_pre:
					output += segment.padding
				output += segment.content
				output += renderer.hl(attr=False)
				output += segment.padding

		return output
