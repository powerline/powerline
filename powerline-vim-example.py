#!/usr/bin/env python
'''Powerline vim statusline example.
'''

from lib.core import Segment
from lib.renderers import VimSegmentRenderer

powerline = Segment([
	Segment('NORMAL', 22, 148, attr=Segment.ATTR_BOLD),
	Segment('⭠ develop', 247, 240),
	Segment([
		Segment(' ~/projects/powerline/lib/'),
		Segment('core.py ', 231, attr=Segment.ATTR_BOLD),
	], 250, 240, divide=False, padding=''),
	Segment('%<%='),
	Segment([
		Segment('unix'),
		Segment('utf-8'),
		Segment('python'),
		Segment(' 83%%', 247, 240),
		Segment([
			Segment(' ⭡ ', 239),
			Segment('23', attr=Segment.ATTR_BOLD),
			Segment(':1 ', 244),
		], 235, 252, divide=False, padding=''),
	], 245, side='r'),
], bg=236)

renderer = VimSegmentRenderer()
stl = powerline.render(renderer)

for group, hl in renderer.hl_groups.items():
	print('hi {group} ctermfg={ctermfg} guifg={guifg} guibg={guibg} ctermbg={ctermbg} cterm={attr} gui={attr}'.format(
		group=group,
		ctermfg=hl['ctermfg'],
		guifg='#{0:06x}'.format(hl['guifg']) if hl['guifg'] != 'NONE' else 'NONE',
		ctermbg=hl['ctermbg'],
		guibg='#{0:06x}'.format(hl['guibg']) if hl['guibg'] != 'NONE' else 'NONE',
		attr=','.join(hl['attr']),
	))

print('let &stl = "{0}"'.format(stl))
