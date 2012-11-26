#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''Powerline terminal prompt example.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.core import Powerline, mksegment
from lib.renderers import TerminalSegmentRenderer

powerline = Powerline([
	mksegment('⭤ SSH', 220, 166, attr=Powerline.ATTR_BOLD),
	mksegment('username', 153, 31),
	mksegment('~', 248, 239),
	mksegment('projects', 248, 239),
	mksegment('powerline', 231, 239, attr=Powerline.ATTR_BOLD),
	mksegment(filler=True),
])

print(powerline.render(TerminalSegmentRenderer()))
