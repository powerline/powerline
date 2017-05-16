# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.segments import with_docstring
from powerline.segments.common.env import CwdSegment
from powerline.lib.unicode import out_u


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
	return [{'contents': str(segment_info['args'].last_exit_code), 'highlight_groups': ['exit_fail']}]


@requires_segment_info
def last_pipe_status(pl, segment_info):
	'''Return last pipe status.

	Highlight groups used: ``exit_fail``, ``exit_success``
	'''
	last_pipe_status = (
		segment_info['args'].last_pipe_status
		or (segment_info['args'].last_exit_code,)
	)
	if any(last_pipe_status):
		return [
			{
				'contents': str(status),
				'highlight_groups': ['exit_fail' if status else 'exit_success'],
				'draw_inner_divider': True
			}
			for status in last_pipe_status
		]
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
	mode = segment_info.get('mode', None)
	if not mode:
		pl.debug('No mode specified')
		return None
	default = default or segment_info.get('default_mode', None)
	if mode == default:
		return None
	try:
		return override[mode]
	except KeyError:
		# Note: with zsh line editor you can emulate as much modes as you wish. 
		# Thus having unknown mode is not an error: maybe just some developer 
		# added support for his own zle widgets. As there is no built-in mode() 
		# function like in VimL and mode is likely be defined by our code or by 
		# somebody knowing what he is doing there is absolutely no need in 
		# keeping translations dictionary.
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
		return [{
			'contents': '',
			'width': 'auto',
			'highlight_groups': ['continuation:current', 'continuation'],
		}]
	ret = []

	for state in segment_info['parser_state'].split():
		state = renames.get(state, state)
		if state:
			ret.append({
				'contents': state,
				'highlight_groups': ['continuation'],
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
		ret[-1]['highlight_groups'] = ['continuation:current', 'continuation']
	else:
		ret[-1].update(width='auto', align='l', highlight_groups=['continuation:current', 'continuation'])

	return ret


@requires_segment_info
class ShellCwdSegment(CwdSegment):
	def get_shortened_path(self, pl, segment_info, use_shortened_path=True, **kwargs):
		if use_shortened_path:
			try:
				return out_u(segment_info['shortened_path'])
			except KeyError:
				pass
		return super(ShellCwdSegment, self).get_shortened_path(pl, segment_info, **kwargs)


cwd = with_docstring(ShellCwdSegment(),
'''Return the current working directory.

Returns a segment list to create a breadcrumb-like effect.

:param int dir_shorten_len:
	shorten parent directory names to this length (e.g. 
	:file:`/long/path/to/powerline` → :file:`/l/p/t/powerline`)
:param int dir_limit_depth:
	limit directory depth to this number (e.g. 
	:file:`/long/path/to/powerline` → :file:`⋯/to/powerline`)
:param bool use_path_separator:
	Use path separator in place of soft divider.
:param bool use_shortened_path:
	Use path from shortened_path ``--renderer-arg`` argument. If this argument 
	is present ``shorten_home`` argument is ignored.
:param bool shorten_home:
	Shorten home directory to ``~``.
:param str ellipsis:
	Specifies what to use in place of omitted directories. Use None to not 
	show this subsegment at all.

Divider highlight group used: ``cwd:divider``.

Highlight groups used: ``cwd:current_folder`` or ``cwd``. It is recommended to define all highlight groups.
''')
