# -*- coding: utf-8 -*-


class Powerline(object):
	def __init__(self, segments):
		'''Create a new Powerline.

		Segments that have empty contents and aren't filler segments are
		dropped from the segment array.
		'''
		self.segments = [segment for segment in segments if segment['contents'] or segment['filler']]

	def render(self, renderer, width=None):
		r = renderer(self.segments)

		return r.render(width)
