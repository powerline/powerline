# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import vim_command_exists
from powerline.theme import requires_segment_info

# coc_status's format: E1 W2
def parse_coc_status(coc_status):
	# type(coc_status) is tuple
	errors_count = 0
	warnings_count = 0
	if len(coc_status) <= 0:
		return errors_count, warnings_count
	status_str = coc_status[0]
	if len(status_str) <= 0:
		return errors_count, warnings_count
	status_list = status_str.split(' ')
	for item in status_list:
		if len(item) > 0 and item[0] == 'E':
			errors_count = int(item[1:])
		if len(item) > 0 and item[0] == 'W':
			warnings_count = int(item[1:])
	return errors_count, warnings_count

@requires_segment_info
def coc(segment_info, pl):
	'''Show whether coc.nvim has found any errors or warnings

	Highlight groups used: ``coc:warning`` or ``warning``, ``coc:error`` or ``error``.
	'''
	segments = []
	if not vim_command_exists('CocCommand'):
		return segments
	coc_status = vim.eval('coc#status()'),
	errors_count, warnings_count = parse_coc_status(coc_status)
	if errors_count > 0:
		segments.append({
			'contents': 'E:' + str(errors_count),
			'highlight_groups': ['coc:error', 'error'],
		})
	if warnings_count > 0:
		segments.append({
			'contents': 'W:' + str(warnings_count),
			'highlight_groups': ['coc:warning', 'warning'],
	})
	return segments
