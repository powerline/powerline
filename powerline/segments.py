# -*- coding: utf-8 -*-

from importlib import import_module
import sys


class Segments(object):
	def __init__(self, ext, path, colorscheme):
		self.ext = ext
		self.path = path
		self.colorscheme = colorscheme

	def get_function(self, segment):
		oldpath = sys.path
		sys.path = self.path + sys.path
		segment_module = str(segment.get('module', 'powerline.ext.{0}.segments'.format(self.ext)))
		try:
			return None, getattr(import_module(segment_module), segment['name']), '{0}.{1}'.format(segment_module, segment['name'])
		finally:
			sys.path = oldpath

	@staticmethod
	def get_string(segment):
		return segment.get('contents'), None, None

	@staticmethod
	def get_filler(segment):
		return None, None, None

	def get(self, segment, side):
		segment_type = segment.get('type', 'function')
		try:
			contents, contents_func, key = getattr(self, 'get_{0}'.format(segment_type))(segment)
		except AttributeError:
			raise TypeError('Unknown segment type: {0}'.format(segment_type))
		highlighting_group = segment.get('highlight', segment.get('name'))
		return {
			'key': key,
			'type': segment_type,
			'highlight': self.colorscheme.get_group_highlighting(highlighting_group),
			'before': segment.get('before', ''),
			'after': segment.get('after', ''),
			'contents_func': contents_func,
			'contents': contents,
			'args': segment.get('args', {}),
			'ljust': segment.get('ljust', False),
			'rjust': segment.get('rjust', False),
			'priority': segment.get('priority', -1),
			'draw_divider': segment.get('draw_divider', True),
			'side': side,
			'exclude_modes': segment.get('exclude_modes', []),
			'include_modes': segment.get('include_modes', []),
			}
