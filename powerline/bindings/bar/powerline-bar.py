#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import time

from threading import Lock, Timer
from argparse import ArgumentParser

from powerline.lemonbar import LemonbarPowerline
from powerline.lib.encoding import get_unicode_writer


if __name__ == '__main__':
	parser = ArgumentParser(description='Powerline lemonbar bindings.')
	parser.add_argument(
		'--i3', action='store_true',
		help='Subscribe for i3 events.'
	)
	args = parser.parse_args()
	powerline = LemonbarPowerline()
	powerline.update_renderer()
	powerline.pl.warn("The 'bar' bindings are deprecated, please switch to 'lemonbar'")
	lock = Lock()
	modes = ['default']
	write = get_unicode_writer(encoding='utf-8')

	def render(reschedule=False):
		if reschedule:
			Timer(0.5, render, kwargs={'reschedule': True}).start()

		global lock
		with lock:
			write(powerline.render(mode=modes[0]))
			write('\n')
			sys.stdout.flush()

	def update(evt):
		modes[0] = evt.change
		render()

	render(reschedule=True)

	if args.i3:
		try:
			import i3ipc
		except ImportError:
			import i3
			i3.Subscription(lambda evt, data, sub: print(render()), 'workspace')
		else:
			conn = i3ipc.Connection()
			conn.on('workspace::focus', lambda conn, evt: render())
			conn.on('mode', lambda conn, evt: update(evt))
			conn.main()

	while True:
		time.sleep(1e8)
