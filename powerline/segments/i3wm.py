# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from threading import Thread

from powerline.segments import Segment, with_docstring


conn = None
try:
    import i3ipc
except ImportError:
    import i3 as conn


def calcgrp(w):
	group = []
	if w['focused']:
		group.append('w_focused')
	if w['urgent']:
		group.append('w_urgent')
	if w['visible']:
		group.append('w_visible')
	group.append('workspace')
	return group


def workspaces(pl, strip=0):
	'''Return list of used workspaces

	:param int strip:
		Specifies how many characters from the front of each workspace name should
		be stripped (e.g. to remove workspace numbers). Defaults to zero.

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``
	'''
	global conn
	if not conn: conn = i3ipc.Connection()

	return [{
		'contents': w['name'][min(len(w['name']),strip):],
		'highlight_groups': calcgrp(w)
	} for w in conn.get_workspaces()]

class ModeSegment(Segment):
	def startup(self, pl, shutdown_event):
		self.mode = 'default'

		def callback(conn, e):
			self.mode = e.change

		conn = i3ipc.Connection()
		conn.on('mode', callback)
		self.thread = Thread(target=conn.main)
		self.thread.daemon = True
		self.thread.start()

	def __call__(self, pl, default=None):
		if self.mode == 'default':
			return default
		return self.mode


mode = with_docstring(ModeSegment(),
'''Returns the current i3 mode

:param str default:
	Specifies the name to be displayed instead of "default".
	By default the segment is left out in the default mode.

Highligh groups used: ``mode``
''')
