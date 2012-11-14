#!/usr/bin/env python
'''Powerline vim statusline example.
'''

from lib.core import Segment
from lib.renderers import VimSegmentRenderer

powerline = Segment([
	Segment('NORMAL', 22, 148, attr=Segment.ATTR_BOLD),
	Segment('⭠ develop', 247, 240, priority=10),
	Segment([
		Segment(' ~/projects/powerline/lib/', draw_divider=False),
		Segment('core.py ', 231, attr=Segment.ATTR_BOLD),
	], 250, 240, padding=''),
	Segment('%=%<', filler=True),
	Segment([
		Segment('unix', priority=50),
		Segment('utf-8', priority=50),
		Segment('python', priority=50),
		Segment('83%', 247, 240, priority=30),
		Segment([
			Segment('⭡', 239),
			Segment('23', attr=Segment.ATTR_BOLD, padding='', draw_divider=False),
			Segment(':1', 244, priority=30, padding='', draw_divider=False),
		], 235, 252),
	], 245, side='r'),
], bg=236)

renderer = VimSegmentRenderer()
stl = powerline.render(renderer)

print(renderer.get_hl_statements())
print('let &stl = "{0}"'.format(stl))
