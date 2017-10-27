# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_global_exists
from powerline.theme import requires_segment_info


@requires_segment_info
def ale(segment_info, pl, err_format='ERR: ln {first_line} ({num}) ', warn_format='WARN: ln {first_line} ({num}) '):
	'''Show whether ALE has found any errors or warnings

	:param str err_format:
		Format string for errors.

	:param str warn_format:
		Format string for warnings.

	Highlight groups used: ``ale:warning`` or ``warning``, ``ale:error`` or ``error``.
	'''
	if not (vim_global_exists('ale_enabled') and int(vim.eval('g:ale_enabled'))):
		return None
	has_errors = int(vim.eval('ale#statusline#Count(' + str(segment_info['bufnr']) + ').total'))
	if not has_errors:
		return
	error = None
	warning = None
	errors_count = 0
	warnings_count = 0
	for issue in vim.eval('ale#engine#GetLoclist(' + str(segment_info['bufnr']) + ')'):
		if issue['type'] == 'E':
			error = error or issue
			errors_count += 1
		elif issue['type'] == 'W':
			warning = warning or issue
			warnings_count += 1
	segments = []
	if error:
		segments.append({
			'contents': err_format.format(first_line=error['lnum'], num=errors_count),
			'highlight_groups': ['ale:error', 'error'],
		})
	if warning:
		segments.append({
			'contents': warn_format.format(first_line=warning['lnum'], num=warnings_count),
			'highlight_groups': ['ale:warning', 'warning'],
		})
	return segments
