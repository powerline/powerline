# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.editors import EditorFunc, EditorTernaryOp, with_input


@with_input((
	'syntastic_errors',
	(EditorTernaryOp(
		EditorFunc('eval',
		           'exists("g:SyntasticLoclist") '
		           '&& g:SyntasticLoclist.current().hasErrorsOrWarningsToDisplay()'),
		EditorFunc('eval',
		           '[g:SyntasticLoclist.current().errors(),'
		           ' g:SyntasticLoclist.current().warnings()]'),
		0,
	),),
	'literal',
))
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
	errs = segment_info['input']['syntastic_errors']
	if not isinstance(errs, list):
		return None
	errors, warnings = errs
	segments = []
	if errors:
		segments.append({
			'contents': err_format.format(first_line=int(errors[0]['lnum']), num=len(errors)),
			'highlight_groups': ['syntastic:error', 'error'],
		})
	if warnings:
		segments.append({
			'contents': warn_format.format(first_line=int(warnings[0]['lnum']), num=len(warnings)),
			'highlight_groups': ['syntastic:warning', 'warning'],
		})
	return segments
