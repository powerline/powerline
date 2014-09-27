# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.bindings.tmux import get_tmux_output


def attached_clients(pl, minimum=1):
	'''Return the number of tmux clients attached to the currently active session

	:param int minimum:
		The minimum number of attached clients that must be present for this 
		segment to be visible.
	'''
	session_output = get_tmux_output(pl, 'list-panes', '-F', '#{session_name}')
	if not session_output:
		return None
	session_name = session_output.rstrip().split('\n')[0]

	attached_clients_output = get_tmux_output(pl, 'list-clients', '-t', session_name)
	attached_count = len(attached_clients_output.rstrip().split('\n'))

	return None if attached_count < minimum else str(attached_count)
