# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import operator

from collections import defaultdict

try:
	from __builtin__ import reduce
except ImportError:
	from functools import reduce

from pygments.token import Token
from prompt_toolkit.styles import DynamicStyle, Attrs

from powerline.renderers.ipython import IPythonRenderer
from powerline.ipython import IPythonInfo
from powerline.colorscheme import ATTR_BOLD, ATTR_ITALIC, ATTR_UNDERLINE


PowerlinePromptToken = Token.Generic.Prompt.Powerline


# Note: since 2.7 there is dict.__missing__ with same purpose. But in 2.6 one 
# must use defaultdict to get __missing__ working.
class PowerlineStyleDict(defaultdict):
	'''Dictionary used for getting pygments style for Powerline groups
	'''
	def __new__(cls, missing_func):
		return defaultdict.__new__(cls)

	def __init__(self, missing_func):
		super(PowerlineStyleDict, self).__init__()
		self.missing_func = missing_func

	def __missing__(self, key):
		return self.missing_func(key)


class PowerlinePromptStyle(DynamicStyle):
	def get_attrs_for_token(self, token):
		if (
			token not in PowerlinePromptToken
			or len(token) != len(PowerlinePromptToken) + 1
			or not token[-1].startswith('Pl')
			or token[-1] == 'Pl'
		):
			return super(PowerlinePromptStyle, self).get_attrs_for_token(token)
		ret = {
			'color': None,
			'bgcolor': None,
			'bold': None,
			'underline': None,
			'italic': None,
			'reverse': False,
			'blink': False,
		}
		for prop in token[-1][3:].split('_'):
			if prop[0] == 'a':
				ret[prop[1:]] = True
			elif prop[0] == 'f':
				ret['color'] = prop[1:]
			elif prop[0] == 'b':
				ret['bgcolor'] = prop[1:]
		return Attrs(**ret)

	def get_token_to_attributes_dict(self):
		dct = super(PowerlinePromptStyle, self).get_token_to_attributes_dict()

		def fallback(key):
			try:
				return dct[key]
			except KeyError:
				return self.get_attrs_for_token(key)

		return PowerlineStyleDict(fallback)

	def invalidation_hash(self):
		return super(PowerlinePromptStyle, self).invalidation_hash() + 1


class IPythonPygmentsRenderer(IPythonRenderer):
	reduce_initial = []

	def get_segment_info(self, segment_info, mode):
		return super(IPythonPygmentsRenderer, self).get_segment_info(
			IPythonInfo(segment_info), mode)

	@staticmethod
	def hl_join(segments):
		return reduce(operator.iadd, segments, [])

	def hl(self, contents, fg=None, bg=None, attrs=None):
		'''Output highlighted chunk.

		This implementation outputs a list containing a single pair 
		(:py:class:`pygments.token.Token`, 
		:py:class:`powerline.lib.unicode.unicode`).
		'''
		guifg = None
		guibg = None
		attrs = []
		if fg is not None and fg is not False:
			guifg = fg[1]
		if bg is not None and bg is not False:
			guibg = bg[1]
		if attrs:
			attrs = []
			if attrs & ATTR_BOLD:
				attrs.append('bold')
			if attrs & ATTR_ITALIC:
				attrs.append('italic')
			if attrs & ATTR_UNDERLINE:
				attrs.append('underline')
		name = (
			'Pl'
			+ ''.join(('_a' + attr for attr in attrs))
			+ (('_f%6x' % guifg) if guifg is not None else '')
			+ (('_b%6x' % guibg) if guibg is not None else '')
		)
		return [(getattr(Token.Generic.Prompt.Powerline, name), contents)]

	def hlstyle(self, **kwargs):
		return []

	def get_client_id(self, segment_info):
		return id(self)


renderer = IPythonPygmentsRenderer
