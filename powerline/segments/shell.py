# vim:fileencoding=utf-8:noet

from powerline.theme import requires_segment_info


@requires_segment_info
def last_status(pl, segment_info):
	'''Return last exit code.

	Highlight groups used: ``exit_fail``
	'''
	if not segment_info['args'].last_exit_code:
		return None
	return [{'contents': str(segment_info['args'].last_exit_code), 'highlight_group': 'exit_fail'}]


@requires_segment_info
def last_pipe_status(pl, segment_info):
	'''Return last pipe status.

	Highlight groups used: ``exit_fail``, ``exit_success``
	'''
	last_pipe_status = segment_info['args'].last_pipe_status
	if any(last_pipe_status):
		return [{'contents': str(status), 'highlight_group': 'exit_fail' if status else 'exit_success', 'draw_inner_divider': True}
			for status in last_pipe_status]
	else:
		return None
