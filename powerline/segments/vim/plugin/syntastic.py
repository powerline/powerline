# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.segments.vim import window_cached
from powerline.bindings.vim import vim_global_exists


@window_cached
@requires_segment_info
def syntastic(pl, segment_info,
              err_format='ERR:  {first_line} ({num}) ',
              warn_format='WARN:  {first_line} ({num}) '):
	'''Show whether syntastic has found any errors or warnings

	:param str err_format:
		Format string for errors.

	:param str warn_format:
		Format string for warnings.

	Highlight groups used: ``syntastic:warning`` or ``warning``, ``syntastic:error`` or ``error``.
	'''
	vim = segment_info['vim']
	if not vim_global_exists(vim, 'SyntasticLoclist'):
		return None
	has_errors = int(vim.eval('g:SyntasticLoclist.current().hasErrorsOrWarningsToDisplay()'))
	if not has_errors:
		return
	errors = vim.eval('g:SyntasticLoclist.current().errors()')
	warnings = vim.eval('g:SyntasticLoclist.current().warnings()')
	segments = []
	if errors:
		segments.append({
			'contents': err_format.format(first_line=errors[0]['lnum'], num=len(errors)),
			'highlight_groups': ['syntastic:error', 'error'],
		})
	if warnings:
		segments.append({
			'contents': warn_format.format(first_line=warnings[0]['lnum'], num=len(warnings)),
			'highlight_groups': ['syntastic:warning', 'warning'],
		})
	return segments
