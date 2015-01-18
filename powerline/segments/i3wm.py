# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import i3


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


def workspaces(pl):
	'''Return workspace list

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``
	'''
	return [{
		'contents': w['name'],
		'highlight_groups': calcgrp(w)
	} for w in i3.get_workspaces()]
