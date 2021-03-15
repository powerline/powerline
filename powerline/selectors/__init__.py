# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import layered_selector, recursive_selector

@layered_selector
def mode(target_modes):
	'''Returns True if the current mode to is contained in ``target_mode``

	:param list target_modes:
		The modes to filter.
	'''

	return lambda pl, segment_info, mode: (
			mode in target_mode
		)

@layered_selector
@recursive_selector
def all_of(**kwargs):
	'''Checks whether all of the given conditions are satisfied

	:param args condition:
		Any argument passed to this selector will be interpreted as a selector on its own that may have arguments.
	'''

	return lambda pl, segment_info, mode: (
			all([func(pl=pl, segment_info=segment_info, mode=mode) for arg, func in kwargs.items() if func])
		)

@layered_selector
@recursive_selector
def any_of(**kwargs):
	'''Checks whether any of the given conditions are satisfied

	:param kwargs condition:
		Any argument passed to this selector will be interpreted as a selector on its own that may have arguments.
	'''

	return lambda pl, segment_info, mode: (
			any([func(pl=pl, segment_info=segment_info, mode=mode) for arg, func in kwargs.items() if func])
		)

