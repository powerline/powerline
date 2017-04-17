# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from mercurial import hg, ui, match

from powerline.lib.vcs import get_branch_name, get_file_status
from powerline.lib.path import join
from powerline.lib.encoding import get_preferred_file_contents_encoding


def branch_name_from_config_file(directory, config_file):
	try:
		with open(config_file, 'rb') as f:
			raw = f.read()
		return raw.decode(get_preferred_file_contents_encoding(), 'replace').strip()
	except Exception:
		return 'default'


class Repository(object):
	__slots__ = ('directory', 'ui', 'create_watcher')

	statuses = 'MARDUI'
	repo_statuses = (1, 1, 1, 1, 2)
	repo_statuses_str = (None, 'D ', ' U', 'DU')

	def __init__(self, directory, create_watcher):
		self.directory = os.path.abspath(directory)
		self.ui = ui.ui()
		self.create_watcher = create_watcher

	def _repo(self, directory):
		# Cannot create this object once and use always: when repository updates
		# functions emit invalid results
		return hg.repository(self.ui, directory)

	def status(self, path=None):
		'''Return status of repository or file.

		Without file argument: returns status of the repository:

		:'D?': dirty (tracked modified files: added, removed, deleted, modified),
		:'?U': untracked-dirty (added, but not tracked files)
		:None: clean (status is empty)

		With file argument: returns status of this file: `M`odified, `A`dded,
		`R`emoved, `D`eleted (removed from filesystem, but still tracked),
		`U`nknown, `I`gnored, (None)Clean.
		'''
		if path:
			return get_file_status(
				directory=self.directory,
				dirstate_file=join(self.directory, '.hg', 'dirstate'),
				file_path=path,
				ignore_file_name='.hgignore',
				get_func=self.do_status,
				create_watcher=self.create_watcher,
			)
		return self.do_status(self.directory, path)

	def do_status(self, directory, path):
		repo = self._repo(directory)
		if path:
			m = match.match(None, None, [path], exact=True)
			statuses = repo.status(match=m, unknown=True, ignored=True)
			for status, paths in zip(self.statuses, statuses):
				if paths:
					return status
			return None
		else:
			resulting_status = 0
			for status, paths in zip(self.repo_statuses, repo.status(unknown=True)):
				if paths:
					resulting_status |= status
			return self.repo_statuses_str[resulting_status]

	def branch(self):
		config_file = join(self.directory, '.hg', 'branch')
		return get_branch_name(
			directory=self.directory,
			config_file=config_file,
			get_func=branch_name_from_config_file,
			create_watcher=self.create_watcher,
		)
