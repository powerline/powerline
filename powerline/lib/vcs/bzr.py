# vim:fileencoding=utf-8:noet
from __future__ import absolute_import, unicode_literals, division, print_function

import sys
from io import StringIO

from bzrlib import (branch, workingtree, status, library_state, trace, ui)


class CoerceIO(StringIO):
	def write(self, arg):
		if isinstance(arg, bytes):
			arg = arg.decode('utf-8', 'replace')
		return super(CoerceIO, self).write(arg)


class Repository(object):
	def __init__(self, directory):
		if isinstance(directory, bytes):
			directory = directory.decode(sys.getfilesystemencoding() or sys.getdefaultencoding() or 'utf-8')
		self.directory = directory
		self.state = library_state.BzrLibraryState(ui=ui.SilentUIFactory, trace=trace.DefaultConfig())

	def status(self, path=None):
		'''Return status of repository or file.

		Without file argument: returns status of the repository:

		:"D?": dirty (tracked modified files: added, removed, deleted, modified),
		:"?U": untracked-dirty (added, but not tracked files)
		:None: clean (status is empty)

		With file argument: returns status of this file: The status codes are
		those returned by bzr status -S
		'''
		try:
			return self._status(path)
		except:
			pass

	def _status(self, path):
		buf = CoerceIO()
		w = workingtree.WorkingTree.open(self.directory)
		status.show_tree_status(w, specific_files=[path] if path else None, to_file=buf, short=True)
		raw = buf.getvalue()
		if not raw.strip():
			return
		if path:
			return raw[:2]
		dirtied = untracked = ' '
		for line in raw.splitlines():
			if len(line) > 1 and line[1] in 'ACDMRIN':
				dirtied = 'D'
			elif line and line[0] == '?':
				untracked = 'U'
		ans = dirtied + untracked
		return ans if ans.strip() else None

	def branch(self):
		try:
			b = branch.Branch.open(self.directory)
			return b._get_nick(local=True) or None
		except:
			pass
