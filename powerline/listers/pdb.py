# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info


@requires_segment_info
def frame_lister(pl, segment_info, full_stack=False, maxframes=3):
	'''List all frames in segment_info format

	:param bool full_stack:
		If true, then all frames in the stack are listed. Normally N first 
		frames are discarded where N is a number of frames present at the first 
		invocation of the prompt minus one.
	:param int maxframes:
		Maximum number of frames to display.
	'''
	if full_stack:
		initial_stack_length = 0
		frames = segment_info['pdb'].stack
	else:
		initial_stack_length = segment_info['initial_stack_length']
		frames = segment_info['pdb'].stack[initial_stack_length:]

	if len(frames) > maxframes:
		frames = frames[-maxframes:]

	return (
		(
			{
				'curframe': frame[0],
				'initial_stack_length': initial_stack_length,
			},
			{}
		)
		for frame in frames
	)
