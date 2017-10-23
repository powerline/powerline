# vim:fileencoding=utf-8:noet
"""
Asynchronous Lint Engine (ALE) plugin

Largely adapted from Sytastic plugin
"""

from __future__ import (
	unicode_literals, division, absolute_import, print_function
)
try:
	import vim
except ImportError:
	vim = object()
from powerline.bindings.vim import vim_global_exists
from powerline.theme import requires_segment_info


# To turn on logging, in the Powerline configuration fie config.json,
# in the "common" key, add log_file and log_level key-value pairs as
# appropriate and desired, for example:
#
# "common": {
#	  "term_truecolor": false,
#	  "log_file": "/mylogdir/powerline.log",
#	  "log_level": "INFO"
# },
#
# and then turn on debug internal variable to True
@requires_segment_info
def ale(
	segment_info,
	pl,
	err_format='ERR:  {first_line} ({num}) ',
	warn_format='WARN:  {first_line} ({num}) '
):
	"""
	Show whether Asynchronous Lint Engine (ALE) has found any errors
	or warnings

	:param str err_format:
		Format string for errors.

	:param str warn_format:
		Format string for warnings.

	Highlight groups used: ``ale:warning`` or
	``warning``, ``ale:error`` or ``error``.
	"""
	# pylint: disable=C0103,W0613
	debug = False
	bufnr = str(segment_info['bufnr'])
	ale_enabled_exists = vim_global_exists('ale_enabled')
	ale_enabled = ale_enabled_exists and int(vim.eval('g:ale_enabled'))
	if debug:
		pl.info('ale_enabled_exists: {0}'.format(ale_enabled_exists))
		pl.info('ale_enabled: {0}'.format(ale_enabled))
	if not ale_enabled:
		return None
	cmd = 'ale#statusline#Count({0}).total'.format(bufnr)
	if debug:
		pl.info('cmd: {0}'.format(cmd))
	has_errors = int(vim.eval(cmd))
	if debug:
		pl.info('has_errors: {0}'.format(has_errors))
	if not has_errors:
		return
	cmd = 'ale#engine#GetLoclist({0})'.format(bufnr)
	if debug:
		pl.info('cmd: {0}'.format(cmd))
	issues = vim.eval(cmd)
	errors, warnings = [], []
	for issue in issues:
		if issue['type'] == 'E':
			errors.append(issue)
		elif issue['type'] == 'W':
			warnings.append(issue)
	segments = []
	if errors:
		segments.append(
			{
				'contents': err_format.format(
					first_line=errors[0]['lnum'], num=len(errors)
				),
				'highlight_groups': ['ale:error', 'error'],
			}
		)
	if warnings:
		segments.append(
			{
				'contents': warn_format.format(
					first_line=warnings[0]['lnum'], num=len(warnings)
				),
				'highlight_groups': ['ale:warning', 'warning'],
			}
		)
	return segments
