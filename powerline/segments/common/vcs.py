# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lib.vcs import guess, tree_status
from powerline.segments import Segment, with_docstring
from powerline.theme import requires_segment_info, requires_filesystem_watcher


@requires_filesystem_watcher
@requires_segment_info
class VCSInfoSegment(Segment):
	divider_highlight_group = None

	@staticmethod
	def get_directory(segment_info):
		return segment_info['getcwd']()

	@staticmethod
	def is_dirty(pl, repo):
		try:
			status = tree_status(repo, pl)
		except Exception as e:
			pl.exception('Failed to compute tree status: {0}', str(e))
			status = '?'
		else:
			status = status and status.strip()
			if status in ignore_statuses:
				return False
		return bool(status)

	def get_highlight_group(self, pl, repo, name, status_colors=False, ignore_statuses=(), **kwargs):
		scol = ['vcsinfo:' + name, 'vcsinfo']
		if status_colors:
			scol.insert(0, 'vcsinfo:clean' if self.is_dirty(pl, repo) else 'vcsinfo:dirty')
		return scol

	def get_property(self, pl, repo, name, **kwargs):
		return [{
			'contents': getattr(repo, name),
			'highlight_group': self.get_highlight_group(pl, repo, name, **kwargs),
			'divider_highlight_group': self.divider_highlight_group
		}]

	def __call__(self, pl, segment_info, create_watcher, **kwargs):
		directory = self.get_directory(segment_info)
		if directory:
			repo = guess(path=directory, create_watcher=create_watcher)
			if repo is not None:
				return self.get_property(pl, repo, **kwargs)
		return None

	def argspecobjs(self):
		yield '__call__', self.__call__
		yield 'get_property', self.get_property
		yield 'get_highlight_group', self.get_highlight_group

	omitted_method_args = {
		'__call__': (0,),
		'get_property': (0, 1, 2,),
		'get_highlight_group': (0, 1, 2,),
	}

	def omitted_args(self, name, method):
		return self.omitted_method_args[name]


vcsinfo = with_docstring(VCSInfoSegment(),
'''Return the current revision info

:param str name:
	Determines what property should be used. Valid values:

	========  ===================================================
	Name      Description
	========  ===================================================
	branch    Current branch name.
	short     Current commit revision abbreviated hex or revno.
	summary   Current commit summary.
	name      Human-readable name of the current revision.
	bookmark  Current bookmark (mercurial) or branch (otherwise).
	========  ===================================================
:param bool status_colors:
	Determines whether repository status will be used to determine highlighting. 
	Default: False.
:param bool ignore_statuses:
	List of statuses which will not result in repo being marked as dirty. Most 
	useful is setting this option to ``["U"]``: this will ignore repository 
	which has just untracked files (i.e. repository with modified, deleted or 
	removed files will be marked as dirty, while just untracked files will make 
	segment show clean repository). Only applicable if ``status_colors`` option 
	is True.

Highlight groups used: ``vcsinfo:clean``, ``vcsinfo:dirty``, ``vcsinfo``.

Additionally ``vcsinfo:{name}`` is used.
''')


@requires_filesystem_watcher
@requires_segment_info
class BranchSegment(VCSInfoSegment):
	def get_highlight_group(self, pl, repo, status_colors=False, ignore_statuses=(), **kwargs):
		scol = ['branch']
		if status_colors:
			scol.insert(0, 'branch_clean' if self.is_dirty(pl, repo) else 'branch_dirty')
		return scol

	def get_property(self, pl, repo, **kwargs):
		return [{
			'contents': repo.branch,
			'highlight_group': self.get_highlight_group(pl, repo, **kwargs),
			'divider_highlight_group': self.divider_highlight_group,
		}]


branch = with_docstring(BranchSegment(),
'''Return the current VCS branch.

:param bool status_colors:
	Determines whether repository status will be used to determine highlighting. 
	Default: False.
:param bool ignore_statuses:
	List of statuses which will not result in repo being marked as dirty. Most 
	useful is setting this option to ``["U"]``: this will ignore repository 
	which has just untracked files (i.e. repository with modified, deleted or 
	removed files will be marked as dirty, while just untracked files will make 
	segment show clean repository). Only applicable if ``status_colors`` option 
	is True.

Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.
''')
