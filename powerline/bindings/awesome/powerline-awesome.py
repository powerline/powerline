#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.bindings.wm import DEFAULT_UPDATE_INTERVAL
from powerline.bindings.wm.awesome import run


def main():
	try:
		interval = float(sys.argv[1])
	except IndexError:
		interval = DEFAULT_UPDATE_INTERVAL
	run(interval=interval)


if __name__ == '__main__':
	main()
