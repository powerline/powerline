#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import time

from threading import Lock

import i3

from powerline import Powerline
from powerline.lib.monotonic import monotonic

if __name__ == '__main__':
	name = 'wm'
	if len(sys.argv) > 1:
		name = sys.argv[1]

	powerline = Powerline( name, renderer_module='bar' )
	powerline.update_renderer()

	interval = 0.5

	lock = Lock()

	def render(event=None, data=None, sub=None):
		global lock
		with lock:
			ln = u'%{l}'
			ln += powerline.render(side='left')
			# ln += u'%{r}'
			ln += powerline.render(side='right')
			print( ln.encode('utf-8') )
			sys.stdout.flush()

	sub = i3.Subscription(render, 'workspace')
	try:
		while True:
			start_time = monotonic()
			render()
			time.sleep(max(interval - (monotonic() - start_time), 0.1))
	except KeyboardInterrupt, e:
		print( "caught" )
		exit()
