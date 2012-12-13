#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''Powerline terminal prompt example.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from powerline.core import Powerline

pl = Powerline('terminal')
print(pl.renderer.render('n'))
