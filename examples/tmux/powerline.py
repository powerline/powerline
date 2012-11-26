#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''Powerline tmux statusline example.

Run with `tmux -f tmux.conf`.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.core import Powerline, mksegment
from lib.renderers import TmuxSegmentRenderer

powerline = Powerline([
	mksegment('⭤ SSH', 220, 166, attr=Powerline.ATTR_BOLD),
	mksegment('username', 153, 31),
	mksegment('23:45', 248, 239),
	mksegment('10.0.0.110', 231, 239, attr=Powerline.ATTR_BOLD),
	mksegment(filler=True, cterm_fg=236, cterm_bg=236),
])

print(powerline.render(TmuxSegmentRenderer()).encode('utf-8'))
