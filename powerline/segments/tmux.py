# vim:fileencoding=utf-8:noet

import os
from subprocess import Popen, PIPE


def attached_clients(pl, minimum=1):
	'''Return the number of tmux clients attached to the currently active session

	:param int minimum:
		The minimum number of attached clients that must be present for this segment to be visible
	'''
	try:
		with open(os.devnull, "w") as devnull:
			find_session_name = ["tmux", "list-panes", "-F", "#{session_name}"]
			session_name_process = Popen(find_session_name, stdout=PIPE, stderr=devnull)
			session_output, err = session_name_process.communicate()

			if 0 == len(session_output):
				return None

			session_name = session_output.rstrip().split(os.linesep)[0]

			find_clients = ["tmux", "list-clients", "-t", session_name]
			attached_clients_process = Popen(find_clients, stdout=PIPE, stderr=devnull)
			attached_clients_output, err = attached_clients_process.communicate()

			attached_count = len(attached_clients_output.rstrip().split(os.linesep))

	except Exception as e:
		sys.stderr.write('Could not execute attached_clients: ({0})\n'.format(e))
		return None

	return None if attached_count < minimum else str(attached_count)
