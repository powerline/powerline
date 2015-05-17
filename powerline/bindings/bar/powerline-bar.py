#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import time

from threading import Lock, Timer
from argparse import ArgumentParser

from powerline import Powerline
from powerline.lib.encoding import get_unicode_writer


class BarPowerline(Powerline):
	get_encoding = staticmethod(lambda: 'utf-8')

	def init(self):
		super(BarPowerline, self).init(ext='wm', renderer_module='bar')


if __name__ == '__main__':
	parser = ArgumentParser(description='Powerline BAR bindings.')
	parser.add_argument(
		'--i3', action='store_true',
		help='Subscribe for i3 events.'
	)
	args = parser.parse_args()
	powerline = BarPowerline()
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
		time.sleep(1e10)
