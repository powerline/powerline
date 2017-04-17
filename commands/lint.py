# vim:fileencoding=utf-8:noet
from __future__ import (division, absolute_import, print_function)

import argparse


def get_argparser(ArgumentParser=argparse.ArgumentParser):
	parser = ArgumentParser(description='Powerline configuration checker.')
	parser.add_argument(
		'-p', '--config-path', action='append', metavar='PATH',
		help='Paths where configuration should be checked, in order. You must '
		     'supply all paths necessary for powerline to work, '
		     'checking partial (e.g. only user overrides) configuration '
		     'is not supported.'
	)
	parser.add_argument(
		'-d', '--debug', action='store_const', const=True,
		help='Display additional information. Used for debugging '
		     '`powerline-lint\' itself, not for debugging configuration.'
	)
	return parser
