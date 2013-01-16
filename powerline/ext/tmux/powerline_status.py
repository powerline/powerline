#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''Powerline tmux statusline.'''
import argparse

try:
	from powerline.core import Powerline
except ImportError:
	import os
	import sys
	sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
	from powerline.core import Powerline

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('side', nargs='?', default='all', choices=('all', 'left', 'right'))
parser.add_argument('--ext', default='tmux')

if __name__ == '__main__':
	args = parser.parse_args()
	pl = Powerline(args.ext)
	segments = pl.renderer.get_theme().get_segments()
	if args.side != 'all':
		segments = [s for s in segments if s['side'] == args.side]
	print(pl.renderer.render('n', segments=segments).encode('utf-8'))
