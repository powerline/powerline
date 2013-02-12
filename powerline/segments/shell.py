# -*- coding: utf-8 -*-

from powerline.theme import requires_segment_info


@requires_segment_info
def last_status(segment_info):
	'''Return last exit code.'''
	return str(segment_info.last_exit_code) if segment_info.last_exit_code else None


@requires_segment_info
def last_pipe_status(segment_info):
	'''Return last pipe status.'''
	if any(segment_info.last_pipe_status):
		return [{"contents": str(status), "highlight_group": "exit_fail" if status else "exit_success"}
			for status in segment_info.last_pipe_status]
	else:
		return None
