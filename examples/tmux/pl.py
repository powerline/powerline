#!/usr/bin/env python2
'''Powerline tmux statusline example.

Run with `tmux -f tmux.conf`.
'''
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from powerline.core import Powerline

parser = argparse.ArgumentParser(description='powerline outputter')
parser.add_argument('side', nargs='?', default='all',
                    choices=('all', 'left', 'right'))
parser.add_argument('--ext', default='tmux')

if __name__ == '__main__':
    args = parser.parse_args()
    pl = Powerline(args.ext)
    segments = pl.renderer.get_theme().get_segments()
    if args.side != 'all':
        segments = [s for s in segments if s['side'] == args.side]
    print(pl.renderer.render('n', segments=segments).encode('utf-8'))
