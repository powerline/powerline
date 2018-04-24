# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, absolute_import)


# Keys are the process Identifiers, values the last Result of is_ssh for this process
_cached_clients = {}

try:
	import psutil
	def is_ssh(pl, segment_info, mode):
		'''Returns True if the ``--process-id`` has sshd as its anchestor.

		Requires the ``psutil`` module.
		'''
		process_id = segment_info['args'].process_id
		if process_id is None:
			pl.warn("Process ID was not passed")
			return False
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
except ImportError:
	pl.warn('Module "psutil" is not installed')
	def is_ssh(pl, segment_info, mode):
		return False

