#!/usr/bin/env python
'''Powerline vim statusline example.
'''

from lib.core import Segment
from lib.renderers import TerminalSegmentRenderer

powerline = Segment([
	Segment('NORMAL', 22, 148, attr=Segment.ATTR_BOLD),
	Segment('⭠ develop', 247, 240),
	Segment([
		Segment(' ~/projects/powerline/lib/'),
		Segment('core.py ', 231, attr=Segment.ATTR_BOLD),
	], 250, 240, separate=False, padding=''),
	Segment(),
	Segment([
		Segment('unix'),
		Segment('utf-8'),
		Segment('python'),
		Segment(' 83%', 247, 240),
		Segment([
			Segment(' ⭡ ', 239),
			Segment('23', attr=Segment.ATTR_BOLD),
			Segment(':1 ', 244),
		], 235, 252, separate=False, padding=''),
	], 245, side='r'),
], bg=236)

print(powerline.render(TerminalSegmentRenderer()))
