# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re

from io import StringIO

from bzrlib import (workingtree, status, library_state, trace, ui)

from powerline.lib.vcs import get_branch_name, get_file_status
from powerline.lib.path import join
from powerline.lib.encoding import get_preferred_file_contents_encoding
from powerline.lib.vcs import BaseRepository
from powerline.lib.unicode import unicode


class CoerceIO(StringIO):
	def write(self, arg):
		if isinstance(arg, bytes):
			arg = arg.decode(get_preferred_file_contents_encoding(), 'replace')
		return super(CoerceIO, self).write(arg)


nick_pat = re.compile(br'nickname\s*=\s*(.+)')


def branch_name_from_config_file(directory, config_file):
	ans = None
	try:
		with open(config_file, 'rb') as f:
			for line in f:
				m = nick_pat.match(line)
				if m is not None:
					ans = m.group(1).strip().decode(get_preferred_file_contents_encoding(), 'replace')
					break
	except Exception:
		pass
	return ans or os.path.basename(directory)


state = None


class Repository(BaseRepository):
	def status(self, path=None):
		'''Return status of repository or file.

		Without file argument: returns status of the repository:

		:'D?': dirty (tracked modified files: added, removed, deleted, modified),
		:'?U': untracked-dirty (added, but not tracked files)
		:None: clean (status is empty)

		With file argument: returns status of this file: The status codes are
		those returned by bzr status -S
		'''
		if path is not None:
			return get_file_status(
				directory=self.directory,
				dirstate_file=join(self.directory, '.bzr', 'checkout', 'dirstate'),
				file_path=path,
				ignore_file_name='.bzrignore',
				get_func=self.do_status,
				create_watcher=self.create_watcher,
			)
		return self.do_status(self.directory, path)

	def do_status(self, directory, path):
		try:
			return self._status(self.directory, path)
		except Exception:
			pass

	def _wt(self, directory=None):
		return workingtree.WorkingTree.open(directory or self.directory)

	def _status(self, directory, path):
		global state
		if state is None:
			state = library_state.BzrLibraryState(ui=ui.SilentUIFactory, trace=trace.DefaultConfig())
		buf = CoerceIO()
		w = self._wt(directory)
		status.show_tree_status(w, specific_files=[path] if path else None, to_file=buf, short=True)
		raw = buf.getvalue()
		if not raw.strip():
			return
		if path:
			ans = raw[:2]
			if ans == 'I ':  # Ignored
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

	@property
	def branch(self):
		config_file = join(self.directory, '.bzr', 'branch', 'branch.conf')
		return get_branch_name(
			directory=self.directory,
			config_file=config_file,
			get_func=branch_name_from_config_file,
			create_watcher=self.create_watcher,
		)

	@property
	def short(self):
		return unicode(self._wt().branch.revno())

	@property
	def summary(self):
		w = self._wt()
		branch = w.branch
		cs = branch.repository.get_revision(branch.get_rev_id(branch.revno()))
		description = cs.message
		try:
			summary = description[:description.index('\n')].strip()
		except ValueError:
			summary = description.strip()
		return summary

	@property
	def name(self):
		return self.short

	@property
	def bookmark(self):
		return self.branch
