# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from powerline.theme import requires_segment_info


@requires_segment_info
def current_line(pl, segment_info):
	'''Displays line number that is next to be run
	'''
	return str(segment_info['curframe'].f_lineno)


@requires_segment_info
def current_file(pl, segment_info, basename=True):
	'''Displays current file name

	:param bool basename:
		If true only basename is displayed.
	'''
	filename = segment_info['curframe'].f_code.co_filename
	if basename:
		filename = os.path.basename(filename)
	return filename


@requires_segment_info
def current_code_name(pl, segment_info):
	'''Displays name of the code object of the current frame
	'''
	return segment_info['curframe'].f_code.co_name


@requires_segment_info
def current_context(pl, segment_info):
	'''Displays currently executed context name

	This is similar to :py:func:`current_code_name`, but gives more details.

	Currently it only gives module file name if code_name happens to be 
	``<module>``.
	'''
	name = segment_info['curframe'].f_code.co_name
	if name == '<module>':
		name = os.path.basename(segment_info['curframe'].f_code.co_filename)
	return name


@requires_segment_info
def stack_depth(pl, segment_info, full_stack=False):
	'''Displays current stack depth

	Result is relative to the stack depth at the time prompt was first run.

	:param bool full_stack:
		If true then absolute depth is used.
	'''
	return str(len(segment_info['pdb'].stack) - (
		0 if full_stack else segment_info['initial_stack_length']))
