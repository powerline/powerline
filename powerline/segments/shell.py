# -*- coding: utf-8 -*-

import os

def last_status(segment_info):
	'''Return last exit code.'''
	return str(segment_info.last_exit_code) if segment_info.last_exit_code else None
last_status.requires_powerline_segment_info = True


def last_pipe_status(segment_info):
	'''Return last pipe status.'''
	if any(segment_info.last_pipe_status):
		return [{"contents": str(status), "highlight_group": "exit_fail" if status else "exit_success"}
			for status in segment_info.last_pipe_status]
	else:
		return None
last_pipe_status.requires_powerline_segment_info = True

def branch_status(with_branch_name=True):
	'''Return the branch for the current repo highlighted based on status.'''
	from powerline.lib.vcs import guess
	repo = guess(os.path.abspath(os.getcwd()))
	if repo:
		ret = []
		branch = repo.branch()
		contents = branch if with_branch_name else ''
		status = 'CURRENT' if not repo.status().strip(' ') else 'MODIFIED'
		ret.append({
			'contents': contents,
			'highlight_group': ['branch_status_' + status, 'branch_status_MODIFIED'],
			})
		return ret
	return None
