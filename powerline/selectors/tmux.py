# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)
from powerline.bindings.tmux import get_tmux_output

# import psutil

_cached_clients = {}


def tmux_via_ssh(pl, segment_info, mode):
	'''Returns True if tmux client is connected via SSH'''
	current_process = psutil.Process()
	try:
		return _cached_clients[current_process.pid]
	except KeyError:
		# Iterate through parents
		while current_process is not None and current_process.pid != 1:
			if current_process.name() == "sshd":
				_cached_clients[current_process.pid] = True
				return True
			current_process = current_process.parent()
		_cached_clients[current_process.pid] = False
		return False
