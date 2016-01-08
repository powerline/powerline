# vim:fileencoding=utf-8:noet
# WARNING: using unicode_literals causes errors in argparse
from __future__ import (division, absolute_import, print_function)

import argparse


def get_argparser(ArgumentParser=argparse.ArgumentParser):
	parser = ArgumentParser(
		description='Powerline BAR bindings.'
	)
	parser.add_argument(
		'--i3', action='store_true',
		help='Subscribe for i3 events.'
	)
	parser.add_argument(
		'--height', default='',
		metavar='PIXELS', help='Bar height.'
	)
	parser.add_argument(
		'--interval', '-i',
		type=float, default=0.5,
		metavar='SECONDS', help='Refresh interval.'
	)
	parser.add_argument(
		'--bar-command', '-C',
		default='lemonbar',
		metavar='CMD', help='Name of the lemonbar executable to use.'
	)
	parser.add_argument(
		'args', nargs=argparse.REMAINDER,
		help='Extra arguments for lemonbar. Should be preceded with ``--`` '
		     'argument in order not to be confused with script own arguments.'
	)
	return parser
