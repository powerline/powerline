# vim:fileencoding=utf-8:noet

from powerline.theme import requires_segment_info


@requires_segment_info
def jobnum(pl, segment_info, show_zero=False):
	'''Return the number of jobs.

	:param bool show_zero:
		If False (default) shows nothing if there are no jobs. Otherwise shows 
		zero for no jobs.
	'''
	jobnum = segment_info['args'].jobnum
	if jobnum is None or (not show_zero and jobnum == 0):
		return None
	else:
		return str(jobnum)


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


@requires_segment_info
def mode(pl, segment_info, override={'vicmd': 'COMMND', 'viins': 'INSERT'}, default=None):
	'''Return the current mode.

	:param dict override:
		dict for overriding mode strings.
	:param str default:
		If current mode is equal to this string then this segment will not get 
		displayed. If not specified the value is taken from 
		``$POWERLINE_DEFAULT_MODE`` variable. This variable is set by zsh 
		bindings for any mode that does not start from ``vi``.
	'''
	mode = segment_info['mode']
	if not mode:
		pl.debug('No or empty _POWERLINE_MODE variable')
		return None
	default = default or segment_info['environ'].get('_POWERLINE_DEFAULT_MODE')
	if mode == default:
		return None
	try:
		return override[mode]
	except KeyError:
		# Note: with zsh line editor you can emulate as much modes as you wish. 
		# Thus having unknown mode is not an error: maybe just some developer 
		# added support for his own zle widgets. As there is no built-in mode() 
		# function like in VimL and _POWERLINE_MODE is likely be defined by our 
		# code or by somebody knowing what he is doing there is absolutely no 
		# need in keeping translations dictionary.
		return mode.upper()


@requires_segment_info
def continuation(pl, segment_info, omit_cmdsubst=True, right_align=False, renames={}):
	'''Display parser state.

	:param bool omit_cmdsubst:
		Do not display cmdsubst parser state if it is the last one.
	:param bool right_align:
		Align to the right.
	:param dict renames:
		Rename states: ``{old_name : new_name}``. If ``new_name`` is ``None`` 
		then given state is not displayed.

	Highlight groups used: ``continuation``, ``continuation:current``.
	'''
	if not segment_info.get('parser_state'):
		return None
	ret = []

	for state in segment_info['parser_state'].split():
		state = renames.get(state, state)
		if state:
			ret.append({
				'contents': state,
				'highlight_group': 'continuation',
				'draw_inner_divider': True,
			})

	if omit_cmdsubst and ret[-1]['contents'] == 'cmdsubst':
		ret.pop(-1)

	if not ret:
		ret.append({
			'contents': ''
		})

	if right_align:
		ret[0].update(width='auto', align='r')
		ret[-1]['highlight_group'] = 'continuation:current'
	else:
		ret[-1].update(width='auto', align='l', highlight_group='continuation:current')

	return ret
