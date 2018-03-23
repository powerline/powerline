# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.bindings.tmux import get_tmux_output
import subprocess
import re

_cached_clients = {}
# This Regex parses pstree -s <Process_ID> information
# It will match, if any process name is sshd
SSHD_REGEX = re.compile(r"(?:^|\W)sshd(?:^|\W)")


def tmux_via_ssh(pl, segment_info, mode, caching=True, default=False):
	'''Returns True if tmux client is connected via SSH
	'''
	pid = get_tmux_output(pl, "display", "-p", "#{client_pid}")
	if not pid.isnumeric():
		return default
	if caching:
		if pid in _cached_clients:
			return _cached_clients[pid]
	try:
		pstree_out = subprocess.check_output(("pstree", "-s", pid)).decode()
	except subprocess.CalledProcessError:
		return default
	# Will be True if a Matcher gets returned ('sshd' is found), 
	# False if None is returned
	is_ssh = bool(SSHD_REGEX.search(pstree_out))
	if caching:
		_cached_clients[pid] = is_ssh
	return is_ssh
