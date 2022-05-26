# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from powerline.theme import requires_segment_info
from powerline.bindings.wm import get_i3_connection

WORKSPACE_REGEX = re.compile(r'^[0-9]+: ?')

def workspace_groups(w):
	group = []
	if w.focused:
		group.append('workspace:focused')
		group.append('w_focused')
	if w.urgent:
		group.append('workspace:urgent')
		group.append('w_urgent')
	if w.visible:
		group.append('workspace:visible')
		group.append('w_visible')
	group.append('workspace')
	return group


def format_name(name, strip=False):
	if strip:
		return WORKSPACE_REGEX.sub('', name, count=1)
	return name


def is_empty_workspace(workspace, containers):
	if workspace.focused or workspace.visible:
		return False
	wins = [win for win in containers[workspace.name].leaves()]
	return False if len(wins) > 0 else True

WS_ICONS = {"multiple": "M"}

def get_icon(workspace, separator, icons, show_multiple_icons, ws_containers):
	icons_tmp = WS_ICONS
	icons_tmp.update(icons)
	icons = icons_tmp

	wins = [win for win in ws_containers[workspace.name].leaves() \
		if win.parent.scratchpad_state == 'none']
	if len(wins) == 0:
		return ''

	result = ''
	cnt = 0
	for key in icons:
		if not icons[key] or len(icons[key]) < 1:
			continue
		if any(key in win.window_class for win in wins if win.window_class):
			result += (separator if cnt > 0 else '') + icons[key]
			cnt += 1
	if not show_multiple_icons and cnt > 1:
		if 'multiple' in icons:
			return icons['multiple']
		else:
			return ''
	return result

@requires_segment_info
def workspaces(pl, segment_info, only_show=None, output=None, strip=0, format='{name}',
	icons=WS_ICONS, sort_workspaces=False, show_output=False, priority_workspaces=[],
	hide_empty_workspaces=False):
	'''Return list of used workspaces

	:param list only_show:
		Specifies which workspaces to show. Valid entries are ``"visible"``,
		``"urgent"`` and ``"focused"``. If omitted or ``null`` all workspaces
		are shown.
	:param str output:
		May be set to the name of an X output. If specified, only workspaces
		on that output are shown. Overrides automatic output detection by
		the lemonbar renderer and bindings.
		Use "__all__" to show workspaces on all outputs.
	:param int strip:
		Specifies how many characters from the front of each workspace name
		should be stripped (e.g. to remove workspace numbers). Defaults to zero.
	:param str format:
		Specifies the format used to display workspaces; defaults to ``{name}``.
		Valid fields are: ``name`` (workspace name), ``number`` (workspace number
		if present), `stipped_name`` (workspace name stripped of leading number),
		``icon`` (if available, icon for application running in the workspace,
		uses the ``multiple`` icon instead of multiple different icons), ``multi_icon``
		(similar to ``icon``, but does not use ``multiple``, instead joins all icons
		with a single space)
	:param dict icons:
		A dictionary mapping a substring of window classes to strings to be used as an
		icon for that window class.
		Further, there is a ``multiple`` icon for workspaces containing more than one
		window.
	:param bool sort_workspaces:
		Sort the workspaces displayed by their name according to the natural ordering.
	:param bool show_output:
		Shows the name of the output if more than one output is connected.
	:param list priority_workspaces:
		A list of workspace names to be sorted before any other workspaces in the given
		order.
	:param bool hide_empty_workspaces:
		Hides all workspaces without any open window.
		Also hides non-focussed workspaces containing only an open scratchpad.


	Highlight groups used: ``workspace`` or ``w_visible``, ``workspace:visible``, ``workspace`` or ``w_focused``, ``workspace:focused``, ``workspace`` or ``w_urgent``, ``workspace:urgent``, ``workspace`` or ``output``.
	'''
	conn = get_i3_connection()

	if not output == "__all__":
		output = output or segment_info.get('output')
	else:
		output = None

	if output:
		output = [output]
	else:
		output = [o.name for o in conn.get_outputs() if o.active]


	def sort_ws(ws):
		if sort_workspaces:
			def natural_key(ws):
				str = ws.name
				return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str)]
			ws = sorted(ws, key=natural_key)
		result = []
		for n in priority_workspaces:
			result += [w for w in ws if w.name == n]
		return result + [w for w in ws if not w.name in priority_workspaces]

	ws_containers = {w_con.name : w_con for w_con in conn.get_tree().workspaces()}

	if len(output) <= 1:
		res = []
		if show_output:
			res += [{
				'contents': output[0],
				'highlight_groups': ['output']
			}]
		res += [{
			'contents': format.format(name = w.name[min(len(w.name), strip):],
				stripped_name = format_name(w.name, strip=True),
				number = w.num,
				icon = get_icon(w, '', icons, False, ws_containers),
				multi_icon = get_icon(w, ' ', icons, True, ws_containers)),
			'highlight_groups': workspace_groups(w)
			} for w in sort_ws(conn.get_workspaces()) \
					if (not only_show or any(getattr(w, tp) for tp in only_show)) \
					if w.output == output[0] \
					if not (hide_empty_workspaces and is_empty_workspace(w, ws_containers))]
		return res
	else:
		res = []
		for n in output:
			if show_output:
				res += [{
					'contents': n,
					'highlight_groups': ['output']
				}]
			res += [{
				'contents': format.format(name = w.name[min(len(w.name), strip):],
					stripped_name = format_name(w.name, strip=True),
					number = w.num,
					icon = get_icon(w, '', icons, False, ws_containers),
					multi_icon = get_icon(w, ' ', icons, True, ws_containers)),
				'highlight_groups': workspace_groups(w)
				} for w in sort_ws(conn.get_workspaces()) \
						if (not only_show or any(getattr(w, tp) for tp in only_show)) \
						if w.output == n \
						if not (hide_empty_workspaces and is_empty_workspace(w, ws_containers))]
		return res

@requires_segment_info
def workspace(pl, segment_info, workspace=None, strip=False, format=None, icons=WS_ICONS):
	'''Return the specified workspace name

	:param str workspace:
		Specifies which workspace to show. If unspecified, may be set by the
		``list_workspaces`` lister if used, otherwise falls back to
		currently focused workspace.

	:param bool strip:
		Specifies whether workspace numbers (in the ``1: name`` format) should
		be stripped from workspace names before being displayed. Defaults to false.
		Deprecated: Use {name} or {stripped_name} of format instead.

	:param str format:
		Specifies the format used to display workspaces; defaults to ``{name}``.
		Valid fields are: ``name`` (workspace name), ``number`` (workspace number
		if present), `stipped_name`` (workspace name stripped of leading number),
		``icon`` (if available, icon for application running in the workspace,
		uses the ``multiple`` icon instead of multiple different icons), ``multi_icon``
		(similar to ``icon``, but does not use ``multiple``, instead joins all icons
		with a single space)

	:param dict icons:
		A dictionary mapping a substring of window classes to strings to be used as an
		icon for that window class.
		Further, there is a ``multiple`` icon for workspaces containing more than one
		window.

	Highlight groups used: ``workspace`` or ``w_visible``, ``workspace:visible``, ``workspace`` or ``w_focused``, ``workspace:focused``, ``workspace`` or ``w_urgent``, ``workspace:urgent``, ``workspace``.
	'''
	if format == None:
		format = '{stripped_name}' if strip else '{name}'

	conn = get_i3_connection()
	ws_containers = {w_con.name : w_con for w_con in conn.get_tree().workspaces()}

	if workspace:
		try:
			w = next((
				w for w in conn.get_workspaces()
				if w.name == workspace
			))
		except StopIteration:
			return None
	elif segment_info.get('workspace'):
		w = segment_info['workspace']
	else:
		try:
			w = next((
				w for w in conn.get_workspaces()
				if w.focused
			))
		except StopIteration:
			return None

	return [{
		'contents': format.format(name = w.name,
			stripped_name = format_name(w.name, strip=True),
			number = w.num,
			icon = get_icon(w, '', icons, False, ws_containers),
			multi_icon = get_icon(w, ' ', icons, True, ws_containers)),
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
		for w in get_i3_connection().get_tree().descendants()
		if w.scratchpad_state != 'none'
	]

def active_window(pl, cutoff=100):
	'''Returns the title of the currently active window.

	:param int cutoff:
		Maximum title length. If the title is longer, the window_class is used instead.

	Highlight groups used: ``active_window_title``.
	'''

	focused = get_i3_connection().get_tree().find_focused()
	cont = focused.name
	if len(cont) > cutoff:
		cont = focused.window_class

	return [{'contents': cont, 'highlight_groups': ['active_window_title']}] if focused.name != focused.workspace().name else []
