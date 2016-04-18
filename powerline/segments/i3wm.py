# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from powerline.theme import requires_segment_info
from powerline.bindings.wm import get_i3_connection


WORKSPACE_REGEX = re.compile(r'^[0-9]+: ?')


def workspace_groups(w):
	group = []
	if w['focused']:
		group.append('w_focused')
	if w['urgent']:
		group.append('w_urgent')
	if w['visible']:
		group.append('w_visible')
	group.append('workspace')
	return group


def format_name(name, strip=False):
	if strip:
		return WORKSPACE_REGEX.sub('', name, count=1)
	return name


@requires_segment_info
def workspaces(pl, segment_info, only_show=None, output=None, strip=0):
	'''Return list of used workspaces

	:param list only_show:
		Specifies which workspaces to show. Valid entries are ``"visible"``, 
		``"urgent"`` and ``"focused"``. If omitted or ``null`` all workspaces 
		are shown.

	:param str output:
		May be set to the name of an X output. If specified, only workspaces 
		on that output are shown. Overrides automatic output detection by 
		the lemonbar renderer and bindings.

	:param int strip:
		Specifies how many characters from the front of each workspace name 
		should be stripped (e.g. to remove workspace numbers). Defaults to zero.

	Highlight groups used: ``workspace`` or ``w_visible``, ``workspace`` or ``w_focused``, ``workspace`` or ``w_urgent``.
	'''
	output = output or segment_info.get('output')

	return [
		{
			'contents': w['name'][strip:],
			'highlight_groups': workspace_groups(w)
		}
		for w in get_i3_connection().get_workspaces()
		if ((not only_show or any(w[typ] for typ in only_show))
		    and (not output or w['output'] == output))
	]


@requires_segment_info
def workspace(pl, segment_info, workspace=None, strip=False):
	'''Return the specified workspace name

	:param str workspace:
		Specifies which workspace to show. If unspecified, may be set by the 
		``list_workspaces`` lister if used, otherwise falls back to 
		currently focused workspace.

	:param bool strip:
		Specifies whether workspace numbers (in the ``1: name`` format) should 
		be stripped from workspace names before being displayed. Defaults to false.

	Highlight groups used: ``workspace`` or ``w_visible``, ``workspace`` or ``w_focused``, ``workspace`` or ``w_urgent``.
	'''
	if workspace:
		try:
			w = next((
				w for w in get_i3_connection().get_workspaces()
				if w['name'] == workspace
			))
		except StopIteration:
			return None
	elif segment_info.get('workspace'):
		w = segment_info['workspace']
	else:
		try:
			w = next((
				w for w in get_i3_connection().get_workspaces()
				if w['focused']
			))
		except StopIteration:
			return None

	return [{
		'contents': format_name(w['name'], strip=strip),
		'highlight_groups': workspace_groups(w)
	}]


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


def scratchpad_groups(w):
	group = []
	if w.urgent:
		group.append('scratchpad:urgent')
	if w.nodes[0].focused:
		group.append('scratchpad:focused')
	if w.workspace().name != '__i3_scratch':
		group.append('scratchpad:visible')
	group.append('scratchpad')
	return group


SCRATCHPAD_ICONS = {
	'fresh': 'O',
	'changed': 'X',
}


def scratchpad(pl, icons=SCRATCHPAD_ICONS):
	'''Returns the windows currently on the scratchpad

	:param dict icons:
		Specifies the strings to show for the different scratchpad window states. Must 
		contain the keys ``fresh`` and ``changed``.

	Highlight groups used: ``scratchpad`` or ``scratchpad:visible``, ``scratchpad`` or ``scratchpad:focused``, ``scratchpad`` or ``scratchpad:urgent``.
	'''

	return [
		{
			'contents': icons.get(w.scratchpad_state, icons['changed']),
			'highlight_groups': scratchpad_groups(w)
		}
		for w in get_i3_connection().get_tree().descendents()
		if w.scratchpad_state != 'none'
	]
