#!/usr/bin/env python
'''Powerline terminal prompt example.
'''

from lib.core import Segment
from lib.renderers import TerminalSegmentRenderer

powerline = Segment([
	Segment('⭤ SSH', 220, 166, attr=Segment.ATTR_BOLD),
	Segment('username', 153, 31),
	Segment([
		Segment('~'),
		Segment('projects'),
		Segment('powerline', 231, attr=Segment.ATTR_BOLD),
	], 248, 239),
])

print(powerline.render(TerminalSegmentRenderer))
