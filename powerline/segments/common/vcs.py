# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lib.vcs import guess, tree_status
from powerline.theme import requires_segment_info, requires_filesystem_watcher


@requires_filesystem_watcher
@requires_segment_info
def branch(pl, segment_info, create_watcher, status_colors=False):
	'''Return the current VCS branch.

	:param bool status_colors:
		determines whether repository status will be used to determine highlighting. Default: False.

	Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.
	'''
	name = segment_info['getcwd']()
	repo = guess(path=name, create_watcher=create_watcher)
	if repo is not None:
		branch = repo.branch()
		scol = ['branch']
		if status_colors:
			try:
				status = tree_status(repo, pl)
			except Exception as e:
				pl.exception('Failed to compute tree status: {0}', str(e))
				status = '?'
			scol.insert(0, 'branch_dirty' if status and status.strip() else 'branch_clean')
		return [{
			'contents': branch,
			'highlight_group': scol,
		}]
