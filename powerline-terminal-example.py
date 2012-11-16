#!/usr/bin/env python
'''Powerline terminal prompt example.
'''

from lib.core import Powerline, Segment
from lib.renderers import TerminalSegmentRenderer

powerline = Powerline([
	Segment('⭤ SSH', 220, 166, attr=Segment.ATTR_BOLD),
	Segment('username', 153, 31),
	Segment('~', 248, 239),
	Segment('projects', 248, 239),
	Segment('powerline', 231, 239, attr=Segment.ATTR_BOLD),
	Segment(filler=True),
])

print(powerline.render(TerminalSegmentRenderer()))
