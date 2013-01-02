try:
	import pygit2 as git

	class Repository(object):
		__slots__ = ('repo', 'directory')

		def __init__(self, directory):
			self.directory = directory
			self.repo = git.Repository(directory)

		def status(self, path=None):
			'''
			Without file argument: returns status of the repository:
			    First column: working directory status (D: dirty / space)
			    Second column: index status (I: index dirty / space)
			    Third column: presense of untracket files (U: untracked files / space)
			    None: repository clean

			With file argument: returns status of this file. Output is equivalent to 
			    the first two columns of "git status --porcelain" (except for merge 
			    statuses as they are not supported by ligbit2).
			'''
			if path:
				status = self.repo.status_file(path)

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
				untracket_column = ' '
				for status in repo.status():
					if status & (git.GIT_STATUS_WT_DELETED
								|git.GIT_STATUS_WT_MODIFIED):
						wt_column = 'D'
					elif status&(git.GIT_STATUS_INDEX_NEW
								|git.GIT_STATUS_INDEX_MODIFIED
								|git.GIT_STATUS_INDEX_DELETED):
						index_column = 'I'
					elif status& git.GIT_STATUS_WT_NEW:
						untracket_column = 'U'
				return wt_column + index_column + untracket_column

		def branch(self):
			try:
				ref = self.repo.lookup_reference('HEAD')
			except KeyError:
				return None

			try:
				target = ref.target
			except ValueError:
				return '[DETACHED HEAD]'

			if target.startswith('refs/heads/'):
				return target[11:]
			else:
				return '[DETACHED HEAD]'

except ImportError:
	from subprocess import Popen, PIPE

	def readlines(cmd, cwd):
		p = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE, cwd=cwd)
		p.stderr.close()
		for line in p.stdout:
			yield line[:-1]

	class Repository(object):
		__slots__ = ('directory',)

		def __init__(self, directory):
			self.directory = directory

		def _gitcmd(self, *args):
			return readlines(('git',)+args, self.directory)

		def status(self, path=None):
			if path:
				try:
					return self._gitcmd('status', '--porcelain', '--', path).next()[:2]
				except StopIteration:
					try:
						self._gitcmd('ls-files', '--ignored', '--exclude-standard', '--others', '--', path).next()
						return '!!'
					except StopIteration:
						return None
			else:
				wt_column = ' '
				index_column = ' '
				untracket_column = ' '
				returns_none = True
				for line in self._gitcmd('status', '--porcelain'):
					if line[0] == '?':
						untracket_column = 'U'
					elif line[0] == '!':
						pass
					elif line[0] != ' ':
						index_column = 'I'
					elif line[1] != ' ':
						wt_column = 'D'
				r = wt_column + index_column + untracket_column
				return None if r == '   ' else r

		def branch(self):
			for line in self._gitcmd('branch', '-l'):
				if line[0] == '*':
					return line[2:]
			return None

# vim: noet ts=4 sts=4 sw=4
