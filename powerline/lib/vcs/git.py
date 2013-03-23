# vim:fileencoding=utf-8:noet

import os
import re
import errno

from powerline.lib.vcs import get_branch_name as _get_branch_name

_ref_pat = re.compile(br'ref:\s*refs/heads/(.+)')

def branch_name_from_config_file(directory, config_file):
	try:
		with open(config_file, 'rb') as f:
			raw = f.read()
	except EnvironmentError:
		return os.path.basename(directory)
	m = _ref_pat.match(raw)
	if m is not None:
		return m.group(1).decode('utf-8', 'replace')
	return '[DETACHED HEAD]'

def get_branch_name(base_dir):
	head = os.path.join(base_dir, '.git', 'HEAD')
	try:
		return _get_branch_name(base_dir, head, branch_name_from_config_file)
	except OSError as e:
		if getattr(e, 'errno', None) == errno.ENOTDIR:
			# We are in a submodule
			return '(no branch)'
		raise

try:
	import pygit2 as git

	class Repository(object):
		__slots__ = ('directory')

		def __init__(self, directory):
			self.directory = directory

		def _repo(self):
			return git.Repository(self.directory)

		def status(self, path=None):
			'''Return status of repository or file.

			Without file argument: returns status of the repository:

			:First column: working directory status (D: dirty / space)
			:Second column: index status (I: index dirty / space)
			:Third column: presense of untracked files (U: untracked files / space)
			:None: repository clean

			With file argument: returns status of this file. Output is
			equivalent to the first two columns of "git status --porcelain"
			(except for merge statuses as they are not supported by libgit2).
			'''
			if path:
				try:
					status = self._repo().status_file(path)
				except (KeyError, ValueError):
					return None

				if status == git.GIT_STATUS_CURRENT:
					return None
				else:
					if status & git.GIT_STATUS_WT_NEW:
						return '??'
					if status & git.GIT_STATUS_IGNORED:
						return '!!'

					if status & git.GIT_STATUS_INDEX_NEW:
						index_status = 'A'
					elif status & git.GIT_STATUS_INDEX_DELETED:
						index_status = 'D'
					elif status & git.GIT_STATUS_INDEX_MODIFIED:
						index_status = 'M'
					else:
						index_status = ' '

					if status & git.GIT_STATUS_WT_DELETED:
						wt_status = 'D'
					elif status & git.GIT_STATUS_WT_MODIFIED:
						wt_status = 'M'
					else:
						wt_status = ' '

					return index_status + wt_status
			else:
				wt_column = ' '
				index_column = ' '
				untracked_column = ' '
				for status in self._repo().status().values():
					if status & git.GIT_STATUS_WT_NEW:
						untracked_column = 'U'
						continue

					if status & (git.GIT_STATUS_WT_DELETED
							| git.GIT_STATUS_WT_MODIFIED):
						wt_column = 'D'

					if status & (git.GIT_STATUS_INDEX_NEW
							| git.GIT_STATUS_INDEX_MODIFIED
							| git.GIT_STATUS_INDEX_DELETED):
						index_column = 'I'
				r = wt_column + index_column + untracked_column
				return r if r != '   ' else None

		def branch(self):
			return get_branch_name(self.directory)
except ImportError:
	from subprocess import Popen, PIPE

	def readlines(cmd, cwd):
		p = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE, cwd=cwd)
		p.stderr.close()
		with p.stdout:
			for line in p.stdout:
				yield line[:-1].decode('utf-8')

	class Repository(object):
		__slots__ = ('directory',)

		def __init__(self, directory):
			self.directory = directory

		def _gitcmd(self, *args):
			return readlines(('git',) + args, self.directory)

		def status(self, path=None):
			if path:
				try:
					return next(self._gitcmd('status', '--porcelain', '--ignored', '--', path))[:2]
				except StopIteration:
					return None
			else:
				wt_column = ' '
				index_column = ' '
				untracked_column = ' '
				for line in self._gitcmd('status', '--porcelain'):
					if line[0] == '?':
						untracked_column = 'U'
						continue
					elif line[0] == '!':
						continue

					if line[0] != ' ':
						index_column = 'I'

					if line[1] != ' ':
						wt_column = 'D'

				r = wt_column + index_column + untracked_column
				return r if r != '   ' else None

		def branch(self):
			return get_branch_name(self.directory)
