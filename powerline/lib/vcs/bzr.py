# vim:fileencoding=utf-8:noet
from __future__ import absolute_import, unicode_literals, division, print_function

import sys
import os
import re
from io import StringIO

from bzrlib import (workingtree, status, library_state, trace, ui)

from powerline.lib.vcs import get_branch_name, get_file_status

class CoerceIO(StringIO):
	def write(self, arg):
		if isinstance(arg, bytes):
			arg = arg.decode('utf-8', 'replace')
		return super(CoerceIO, self).write(arg)

state = None

nick_pat = re.compile(br'nickname\s*=\s*(.+)')

def branch_name_from_config_file(directory, config_file):
	ans = None
	try:
		with open(config_file, 'rb') as f:
			for line in f:
				m = nick_pat.match(line)
				if m is not None:
					ans = m.group(1).strip().decode('utf-8', 'replace')
					break
	except Exception:
		pass
	return ans or os.path.basename(directory)

class Repository(object):

	def __init__(self, directory):
		if isinstance(directory, bytes):
			directory = directory.decode(sys.getfilesystemencoding() or sys.getdefaultencoding() or 'utf-8')
		self.directory = os.path.abspath(directory)

	def status(self, path=None):
		'''Return status of repository or file.

		Without file argument: returns status of the repository:

		:"D?": dirty (tracked modified files: added, removed, deleted, modified),
		:"?U": untracked-dirty (added, but not tracked files)
		:None: clean (status is empty)

		With file argument: returns status of this file: The status codes are
		those returned by bzr status -S
		'''
		if path is not None:
			return get_file_status(self.directory, os.path.join(self.directory, '.bzr', 'checkout', 'dirstate'),
								path, '.bzrignore', self.do_status)
		return self.do_status(self.directory, path)

	def do_status(self, directory, path):
		try:
			return self._status(self.directory, path)
		except Exception:
			pass

	def _status(self, directory, path):
		global state
		if state is None:
			state = library_state.BzrLibraryState(ui=ui.SilentUIFactory, trace=trace.DefaultConfig())
		buf = CoerceIO()
		w = workingtree.WorkingTree.open(directory)
		status.show_tree_status(w, specific_files=[path] if path else None, to_file=buf, short=True)
		raw = buf.getvalue()
		if not raw.strip():
			return
		if path:
			ans = raw[:2]
			if ans == 'I ': # Ignored
				ans = None
			return ans
		dirtied = untracked = ' '
		for line in raw.splitlines():
			if len(line) > 1 and line[1] in 'ACDMRIN':
				dirtied = 'D'
			elif line and line[0] == '?':
				untracked = 'U'
		ans = dirtied + untracked
		return ans if ans.strip() else None

	def branch(self):
		config_file = os.path.join(self.directory, '.bzr', 'branch', 'branch.conf')
		return get_branch_name(self.directory, config_file, branch_name_from_config_file)

