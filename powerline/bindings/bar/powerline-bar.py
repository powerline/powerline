#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import time

from threading import Lock
from argparse import ArgumentParser

from powerline import Powerline
from powerline.lib.monotonic import monotonic
from powerline.lib.encoding import get_unicode_writer


class BarPowerline(Powerline):
	get_encoding = staticmethod(lambda: 'utf-8')

	def init(self):
		super(BarPowerline, self).init(ext='wm', renderer_module='bar')


def render(event=None, data=None, sub=None):
	global lock
	with lock:
		write(powerline.render())
		write('\n')
		sys.stdout.flush()


if __name__ == '__main__':
	parser = ArgumentParser(description='Powerline BAR bindings.')
	parser.add_argument(
		'--i3', action='store_true',
		help='Subscribe for i3 events.'
	)
	args = parser.parse_args()
	powerline = BarPowerline()

	interval = 0.5
	lock = Lock()

	write = get_unicode_writer(encoding='utf-8')

	if args.i3:
		import i3
		sub = i3.Subscription(render, 'workspace')

	while True:
		start_time = monotonic()
		render()
		time.sleep(max(interval - (monotonic() - start_time), 0.1))
