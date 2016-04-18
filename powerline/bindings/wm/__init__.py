# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from powerline.theme import requires_segment_info
from powerline.lib.shell import run_cmd


conn = None


def get_i3_connection():
	'''Return a valid, cached i3 Connection instance
	'''
	global conn
	if not conn:
		try:
			import i3ipc
		except ImportError:
			import i3 as conn
		else:
			conn = i3ipc.Connection()
	return conn


XRANDR_OUTPUT_RE = re.compile(r'^(?P<name>[0-9A-Za-z-]+) connected(?P<primary> primary)? (?P<width>\d+)x(?P<height>\d+)\+(?P<x>\d+)\+(?P<y>\d+)', re.MULTILINE)


def get_connected_xrandr_outputs(pl):
	'''Iterate over xrandr outputs

	Outputs are represented by a dictionary with ``name``, ``width``, 
	``height``, ``primary``, ``x`` and ``y`` keys.
	'''
	return (match.groupdict() for match in XRANDR_OUTPUT_RE.finditer(
	    run_cmd(pl, ['xrandr', '-q'])
	))
