# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from powerline.theme import requires_segment_info
from powerline.lib.shell import run_cmd
from powerline.lib.dict import updated


conn = None
XRANDR_OUTPUT_RE = re.compile(r'^(?P<name>[0-9A-Za-z-]+) connected (?P<width>\d+)x(?P<height>\d+)\+(?P<x>\d+)\+(?P<y>\d+)', re.MULTILINE)
def get_connected_xrandr_outputs(pl):
    return (match.groupdict() for match in XRANDR_OUTPUT_RE.finditer(
        run_cmd(pl, ['xrandr', '-q'])
    ))


@requires_segment_info
def output_lister(pl, segment_info):
	'''List all outputs in segment_info format
	'''

	return (
		(
			updated(segment_info, output=output['name']),
			{
				'draw_inner_divider': None
			}
		)
		for output in get_connected_xrandr_outputs(pl)
	)


@requires_segment_info
def workspace_lister(pl, segment_info, only_show=None, output=None):
	'''List all workspaces in segment_info format

	Sets the segment info values of ``workspace`` and ``output`` to the name of 
	the i3 workspace and the ``xrandr`` output respectively and the keys
	``"visible"``, ``"urgent"`` and ``"focused`` to a boolean indicating these
	states.

	:param list only_show:
		Specifies which workspaces to list. Valid entries are ``"visible"``, 
		``"urgent"`` and ``"focused"``. If omitted or ``null`` all workspaces 
		are listed.

	:param str output:
		May be set to the name of an X output. If specified, only workspaces 
		on that output are listed. Overrides automatic output detection by 
		the lemonbar renderer and bindings. Set to ``false`` to force 
		all workspaces to be shown.
	'''

	if output == None:
		output = output or segment_info.get('output')

	return (
		(
			updated(
				segment_info,
				output=w['output'],
				workspace={
					'name': w['name'],
					'visible': w['visible'],
					'urgent': w['urgent'],
					'focused': w['focused'],
				},
			),
			{
				'draw_inner_divider': None
			}
		)
		for w in conn.get_workspaces()
		if (((not only_show or any(w[typ] for typ in only_show))
		   and (not output or w['output'] == output)))
	)
