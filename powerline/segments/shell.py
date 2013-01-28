# -*- coding: utf-8 -*-


def last_status(segment_info):
	return str(segment_info.last_exit_code) if segment_info.last_exit_code else None
last_status.requires_powerline_segment_info = True


def last_pipe_status(segment_info):
	if any(segment_info.last_pipe_status):
		return [{"contents": str(status), "highlight_group": "exit_fail" if status else "exit_success"}
			for status in segment_info.last_pipe_status]
	else:
		return None
last_pipe_status.requires_powerline_segment_info = True
