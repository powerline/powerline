#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import time
import re
import subprocess

from threading import Lock, Timer
from argparse import ArgumentParser, REMAINDER

from powerline.lemonbar import LemonbarPowerline
from powerline.lib.shell import run_cmd


if __name__ == '__main__':
	parser = ArgumentParser(
		description='Powerline BAR bindings.',
		usage='%(prog)s [-h] [--i3] [--height HEIGHT] [--interval INTERVAL] [--bar-command CMD] -- args'
	)
	parser.add_argument(
		'--i3', action='store_true',
		help='Subscribe for i3 events.'
	)
	parser.add_argument(
		'--height', default='',
		help='Bar height.'
	)
	parser.add_argument(
		'--interval', '-i',
		type=float, default=0.5,
		help='Refresh interval.'
	)
	parser.add_argument(
		'--bar-command', '-c',
		default='lemonbar',
		help='Name of the lemonbar executable to use.'
	)
	parser.add_argument(
		'args', nargs=REMAINDER,
		help='Extra arguments for lemonbar.'
	)
	args = parser.parse_args()

	powerline = LemonbarPowerline()
	powerline.update_renderer()
	bars = []
	active_screens = [match.groupdict() for match in re.finditer(
		'^(?P<name>[0-9A-Za-z-]+) connected (?P<width>\d+)x(?P<height>\d+)\+(?P<x>\d+)\+(?P<y>\d+)',
		run_cmd(powerline.pl, ['xrandr', '-q']),
		re.MULTILINE
	)]

	for screen in active_screens:
		command = [args.bar_command, '-g', '{0}x{1}+{2}'.format(screen['width'], args.height, screen['x'])] + args.args[1:]
		process = subprocess.Popen(command, stdin=subprocess.PIPE)
		bars.append((screen['name'], process, int(screen['width']) / 5))

	lock = Lock()
	modes = ['default']

	def render(reschedule=False):
		if reschedule:
			Timer(args.interval, render, kwargs={'reschedule': True}).start()

		global lock
		with lock:
			for output, process, width in bars:
				process.stdin.write(powerline.render(mode=modes[0], width=width, matcher_info=output).encode('utf-8') + b'\n')
				process.stdin.flush()

	def update(evt):
		modes[0] = evt.change
		render()

	render(reschedule=True)

	if args.i3:
		try:
			import i3ipc
		except ImportError:
			import i3
			i3.Subscription(lambda evt, data, sub: render(), 'workspace')
		else:
			conn = i3ipc.Connection()
			conn.on('workspace::focus', lambda conn, evt: render())
			conn.on('mode', lambda conn, evt: update(evt))
			conn.main()

	while True:
		time.sleep(1e8)
