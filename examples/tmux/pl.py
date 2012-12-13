#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''Powerline tmux statusline example.

Run with `tmux -f tmux.conf`.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from powerline.core import Powerline
from powerline.segment import mksegment
from powerline.ext.tmux import TmuxRenderer

powerline = Powerline([
	mksegment('⭤ SSH', 220, 166, attr=TmuxRenderer.ATTR_BOLD),
	mksegment('username', 153, 31),
	mksegment('23:45', 248, 239),
	mksegment('10.0.0.110', 231, 239, attr=TmuxRenderer.ATTR_BOLD),
	mksegment(filler=True, cterm_fg=236, cterm_bg=236),
])

print(powerline.render(TmuxRenderer).encode('utf-8'))
