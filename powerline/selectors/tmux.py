# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)
from powerline.bindings.tmux import get_tmux_output


_cached_clients = {}

def tmux_via_ssh(pl, segment_info, mode):
	'''Returns True if tmux client is connected via SSH
	
	Requires the ``psutil`` module.
	
	Works only for tmux versions >= 2.1'''
	try:
		import psutil
	except ImportError:
		pl.warn('Module "psutil" is not installed, thus we cannot detect whether tmux is run via ssh')
		return False
	process_id = segment_info['args'].process_id
	if process_id is None:
		pl.warn("Process ID was not passed, maybe you are using tmux version < 2.1")
		return False # or True
	current_process = psutil.Process(segment_info['args'].process_id)
	try:
		return _cached_clients[current_process.pid]
	except KeyError:
		# Iterate through parents
		while current_process is not None and current_process.pid != 1:
			if current_process.name() == 'sshd':
				_cached_clients[current_process.pid] = True
				return True
			current_process = current_process.parent()
		_cached_clients[current_process.pid] = False
		return False
