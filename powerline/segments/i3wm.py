# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info


conn = None


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


def workspaces(pl, only_show=None, strip=0):
	'''Return list of used workspaces

	:param list only_show:
		Specifies which workspaces to show. Valid entries are ``"visible"``, 
		``"urgent"`` and ``"focused"``. If omitted or ``null`` all workspaces 
		are shown.

	:param int strip:
		Specifies how many characters from the front of each workspace name 
		should be stripped (e.g. to remove workspace numbers). Defaults to zero.

	Highlight groups used: ``workspace`` or ``w_visible``, ``workspace`` or ``w_focused``, ``workspace`` or ``w_urgent``.
	'''
	global conn
	if not conn:
		try:
			import i3ipc
		except ImportError:
			import i3 as conn
		else:
			conn = i3ipc.Connection()

	return [{
		'contents': w['name'][min(len(w['name']), strip):],
		'highlight_groups': calcgrp(w)
	} for w in conn.get_workspaces() if not only_show or any((w[typ] for typ in only_show))]


@requires_segment_info
def mode(pl, segment_info, names={'default': None}):
	'''Returns current i3 mode

	:param dict names:
		Specifies the string to show for various modes.
		Use ``null`` to hide a mode (``default`` is hidden by default).

	Highligh groups used: ``mode``
	'''
	mode = segment_info['mode']
	if mode in names:
		return names[mode]
	return mode
