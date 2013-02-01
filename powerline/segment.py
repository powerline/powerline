# -*- coding: utf-8 -*-

from importlib import import_module
import sys


class Segment(object):
	def __init__(self, ext, path, default_module=None):
		self.default_module = default_module or 'powerline.segments.{0}'.format(ext)
		self.path = path

	def get_function(self, segment):
		oldpath = sys.path
		sys.path = self.path + sys.path
		segment_module = str(segment.get('module', self.default_module))
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
			get_segment_info = getattr(self, 'get_{0}'.format(segment_type))
		except AttributeError:
			raise TypeError('Unknown segment type: {0}'.format(segment_type))
		contents, contents_func, key = get_segment_info(segment)
		highlight_group = segment.get('highlight_group', segment.get('name'))
		divider_highlight_group = segment.get('divider_highlight_group')
		return {
			'key': key,
			'type': segment_type,
			'highlight_group': highlight_group,
			'divider_highlight_group': divider_highlight_group,
			'before': segment.get('before', ''),
			'after': segment.get('after', ''),
			'contents_func': contents_func,
			'contents': contents,
			'args': segment.get('args', {}),
			'priority': segment.get('priority', -1),
			'draw_divider': segment.get('draw_divider', True),
			'side': side,
			'exclude_modes': segment.get('exclude_modes', []),
			'include_modes': segment.get('include_modes', []),
			'width': segment.get('width'),
			'align': segment.get('align', 'l'),
			'_rendered_raw': u'',
			'_rendered_hl': u'',
			'_len': 0,
			'_space_left': 0,
			'_space_right': 0,
			}
