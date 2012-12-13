#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''Powerline tmux statusline example.

Run with `tmux -f tmux.conf`.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from powerline.core import Powerline

pl = Powerline('tmux')
print(pl.renderer.render('n').encode('utf-8'))
