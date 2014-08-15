# vim:fileencoding=utf-8:noet

try:
	import vim
except ImportError:
	vim = object()  # NOQA

from powerline.segments.vim import window_cached


@window_cached
def syntastic(pl, err_format='ERR:  {first_line} ({num}) ', warn_format='WARN:  {first_line} ({num}) '):
	'''Show whether syntastic has found any errors or warnings

	:param str err_format:
		Format string for errors.

	:param str warn_format:
		Format string for warnings.

	Highlight groups used: ``syntastic.warning`` or ``warning``, ``syntastic.error`` or ``error``.
	'''
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
			'contents': err_format.format(first_line=errors[0]['lnum'], num=len(errors)),
			'highlight_group': ['syntastic.error', 'error'],
		})
	if warnings:
		segments.append({
			'contents': warn_format.format(first_line=warnings[0]['lnum'], num=len(warnings)),
			'highlight_group': ['syntastic.warning', 'warning'],
		})
	return segments
