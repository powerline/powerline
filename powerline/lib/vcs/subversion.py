# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from pysvn import Client

from powerline.lib.vcs import get_branch_name, get_file_status
from powerline.lib.path import join


class Repository(object):
	def __init__(self, directory, create_watcher):
		self.directory = os.path.abspath(directory)
		self.create_watcher = create_watcher
		self.client = Client()

	def status(self, path=None):
		'''Return status of repository or file.

		Without file argument: returns status of the repository:

		:'D?': dirty (tracked modified files: added, removed, deleted, modified),
		:'?U': untracked-dirty (added, but not tracked files)
		:None: clean (status is empty)

		With file argument: returns status of this file: The status codes are
		those returned by svn status (except for unversioned files where 'U' is
		used instead of '?')
		'''
		if path is not None:
			return get_file_status(
				directory=self.directory,
				dirstate_file=join(self.directory, '.svn', 'wc.db'),
				file_path=path,
				ignore_file_name='',
				get_func=self._status,
				create_watcher=self.create_watcher,
			)
		return self._status(self.directory, path)

	def _status(self, directory, path):
		if path:
			mapping = {
			    'added': 'A',
			    'conflicted': 'C',
			    'deleted': 'D',
			    'modified': 'M',
			    'replaced': 'R',
			    'unversioned': 'U',
			}
			s = self.client.status(join(directory, path))
			if s:
				s = s .pop()
				if str(s.text_status) in mapping:
					return mapping.get(str(s.text_status))
			return None
		dirty = ' '
		untracked = ' '
		for s in self.client.status(directory, get_all=False):
			if str(s.text_status) == 'unversioned':
				untracked = 'U'
			if str(s.text_status) in ('modified', 'added', 'missing', 'deleted', 'replaced', 'merged', 'conflicted'):
				dirty = 'D'
		ans = dirty + untracked
		return ans if ans.strip() else None

	def revision(self, directory, config_file):
		info = self.client.info(directory)
		return '/{path}:r{revision}'.format(
			path=info.get('url')[len(info.get('repos')) + 1:],
			revision=info.get('revision').number
		)

	def branch(self):
		config_file = join(self.directory, '.svn', 'wc.db')
		return get_branch_name(
			directory=self.directory,
			config_file=config_file,
			get_func=self.revision,
			create_watcher=self.create_watcher,
		)
