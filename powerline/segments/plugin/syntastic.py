# vim:fileencoding=utf-8:noet

import vim

from powerline.segments.vim import window_cached


@window_cached
def syntastic(pl):
	if not int(vim.eval('exists("g:SyntasticLoclist")')):
		return
	has_errors = int(vim.eval('g:SyntasticLoclist.current().hasErrorsOrWarningsToDisplay()'))
	if not has_errors:
		return
	errors = vim.eval('g:SyntasticLoclist.current().errors()')
	warnings = vim.eval('g:SyntasticLoclist.current().warnings()')
	segments = []
	if errors:
		segments.append({
			'contents': 'ERR:  {line} ({num}) '.format(line=errors[0]['lnum'], num=len(errors)),
			'highlight_group': ['syntastic.error', 'error', 'background'],
			})
	if warnings:
		segments.append({
			'contents': 'WARN:  {line} ({num}) '.format(line=warnings[0]['lnum'], num=len(warnings)),
			'highlight_group': ['syntastic.warning', 'warning', 'background'],
			})
	return segments
