#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import time

from threading import Lock

from powerline.bindings.wm import get_i3_connection, i3_subscribe

from powerline import Powerline
from powerline.lib.monotonic import monotonic


class I3Powerline(Powerline):
	'''Powerline child for i3bar

	Currently only changes the default log target.
	'''
	default_log_stream = sys.stderr


if __name__ == '__main__':
	name = 'wm'
	if len(sys.argv) > 1:
		name = sys.argv[1]

	powerline = I3Powerline(name, renderer_module='i3bar')
	powerline.update_renderer()

	interval = 0.5

	print ('{"version": 1}')
	print ('[')
	print ('[]')

	lock = Lock()

	def render(event=None, data=None, sub=None):
		global lock
		with lock:
			print (',[' + powerline.render()[:-1] + ']')
			sys.stdout.flush()

	i3 = get_i3_connection()
	i3_subscribe(i3, 'workspace', render)

	while True:
		start_time = monotonic()
		render()
		time.sleep(max(interval - (monotonic() - start_time), 0.1))
