# -*- coding: utf-8 -*-


class Powerline(object):
	def __init__(self, segments):
		'''Create a new Powerline.

		Segments that aren't filler segments and whose contents aren't None are
		dropped from the segment array.
		'''
		self.segments = [segment for segment in segments if segment['contents'] is not None or segment['filler']]

	def render(self, renderer, width=None):
		r = renderer(self.segments)

		return r.render(width)
