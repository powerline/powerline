# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import layered_selector

@layered_selector
def output(target_outputs):
	'''Returns True if the current output rendered to is contained in ``target_output``

	:param list target_outputs:
		The outputs to filter.
	'''

	return lambda pl, segment_info, mode: (
			'output' in segment_info
			and segment_info['output'] in target_outputs
			)

@layered_selector
def channel_full(channel_name):
	'''Returns True while the specified channel exists and is filled with any value.

	:param string channel_name:
		The channel to check.
	'''

	return lambda pl, segment_info, mode: (
			'payloads' in segment_info
			and channel_name in segment_info['payloads']
			and segment_info['payloads'][channel_name]
			)

@layered_selector
def channel_empty(channel_name):
	'''Returns True while the specified channel is empty or does not exist

	:param string channel_name:
		The channel to check.
	'''

	return lambda pl, segment_info, mode: (
			not 'payloads' in segment_info
			or not channel_name in segment_info['payloads']
			or not segment_info['payloads'][channel_name]
			)

@layered_selector
def channel_has_value(channel_name, value):
	'''Returns True while the specified channel is filled with the specified value

	:param string channel_name:
		The channel to check.
	:param string value:
		The value to check against.
	'''

	return lambda pl, segment_info, mode: (
			'payloads' in segment_info
			and channel_name in segment_info['payloads']
			and (
				isinstance(segment_info['payloads'][channel_name], str)
				and segment_info['payloads'][channel_name] == value
				) or (
					len(segment_info['payloads'][channel_name]) == 2
					and segment_info['payloads'][channel_name][0] == value
					)
				)
