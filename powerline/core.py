# -*- coding: utf-8 -*-


class Powerline(object):
	def __init__(self, segments):
		'''Create a new Powerline.

		Segments that aren't filler segments and whose contents aren't None are
		dropped from the segment array.
		'''
		self.renderer = None  # FIXME This should be assigned here based on the current configuration
		self.segments = [segment for segment in segments if segment['contents'] is not None or segment['filler']]

	def render(self, renderer, width=None):
		self.renderer = renderer(self.segments)

		return self.renderer.render(width)
