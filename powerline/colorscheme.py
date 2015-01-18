# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from copy import copy

from powerline.lib.unicode import unicode


DEFAULT_MODE_KEY = None
ATTR_BOLD = 1
ATTR_ITALIC = 2
ATTR_UNDERLINE = 4


def get_attrs_flag(attrs):
	'''Convert an attribute array to a renderer flag.'''
	attrs_flag = 0
	if 'bold' in attrs:
		attrs_flag |= ATTR_BOLD
	if 'italic' in attrs:
		attrs_flag |= ATTR_ITALIC
	if 'underline' in attrs:
		attrs_flag |= ATTR_UNDERLINE
	return attrs_flag


def pick_gradient_value(grad_list, gradient_level):
	'''Given a list of colors and gradient percent, return a color that should be used.

	Note: gradient level is not checked for being inside [0, 100] interval.
	'''
	return grad_list[int(round(gradient_level * (len(grad_list) - 1) / 100))]


class Colorscheme(object):
	def __init__(self, colorscheme_config, colors_config):
		'''Initialize a colorscheme.'''
		self.colors = {}
		self.gradients = {}

		self.groups = colorscheme_config['groups']
		self.translations = colorscheme_config.get('mode_translations', {})

		# Create a dict of color tuples with both a cterm and hex value
		for color_name, color in colors_config['colors'].items():
			try:
				self.colors[color_name] = (color[0], int(color[1], 16))
			except TypeError:
				self.colors[color_name] = (color, cterm_to_hex[color])

		# Create a dict of gradient names with two lists: for cterm and hex 
		# values. Two lists in place of one list of pairs were chosen because 
		# true colors allow more precise gradients.
		for gradient_name, gradient in colors_config['gradients'].items():
			if len(gradient) == 2:
				self.gradients[gradient_name] = (
					(gradient[0], [int(color, 16) for color in gradient[1]]))
			else:
				self.gradients[gradient_name] = (
					(gradient[0], [cterm_to_hex[color] for color in gradient[0]]))

	def get_gradient(self, gradient, gradient_level):
		if gradient in self.gradients:
			return tuple((pick_gradient_value(grad_list, gradient_level) for grad_list in self.gradients[gradient]))
		else:
			return self.colors[gradient]

	def get_group_props(self, mode, trans, group, translate_colors=True):
		if isinstance(group, (str, unicode)):
			try:
				group_props = trans['groups'][group]
			except KeyError:
				try:
					group_props = self.groups[group]
				except KeyError:
					return None
				else:
					return self.get_group_props(mode, trans, group_props, True)
			else:
				return self.get_group_props(mode, trans, group_props, False)
		else:
			if translate_colors:
				group_props = copy(group)
				try:
					ctrans = trans['colors']
				except KeyError:
					pass
				else:
					for key in ('fg', 'bg'):
						try:
							group_props[key] = ctrans[group_props[key]]
						except KeyError:
							pass
				return group_props
			else:
				return group

	def get_highlighting(self, groups, mode, gradient_level=None):
		trans = self.translations.get(mode, {})
		for group in groups:
			group_props = self.get_group_props(mode, trans, group)
			if group_props:
				break
		else:
			raise KeyError('Highlighting groups not found in colorscheme: ' + ', '.join(groups))

		if gradient_level is None:
			pick_color = self.colors.__getitem__
		else:
			pick_color = lambda gradient: self.get_gradient(gradient, gradient_level)

		return {
			'fg': pick_color(group_props['fg']),
			'bg': pick_color(group_props['bg']),
			'attrs': get_attrs_flag(group_props.get('attrs', [])),
		}


#       0         1         2         3         4         5         6         7         8         9
cterm_to_hex = (
	0x000000, 0xc00000, 0x008000, 0x804000, 0x0000c0, 0xc000c0, 0x008080, 0xc0c0c0, 0x808080, 0xff6060,  # 0
	0x00ff00, 0xffff00, 0x8080ff, 0xff40ff, 0x00ffff, 0xffffff, 0x000000, 0x00005f, 0x000087, 0x0000af,  # 1
	0x0000d7, 0x0000ff, 0x005f00, 0x005f5f, 0x005f87, 0x005faf, 0x005fd7, 0x005fff, 0x008700, 0x00875f,  # 2
	0x008787, 0x0087af, 0x0087d7, 0x0087ff, 0x00af00, 0x00af5f, 0x00af87, 0x00afaf, 0x00afd7, 0x00afff,  # 3
	0x00d700, 0x00d75f, 0x00d787, 0x00d7af, 0x00d7d7, 0x00d7ff, 0x00ff00, 0x00ff5f, 0x00ff87, 0x00ffaf,  # 4
	0x00ffd7, 0x00ffff, 0x5f0000, 0x5f005f, 0x5f0087, 0x5f00af, 0x5f00d7, 0x5f00ff, 0x5f5f00, 0x5f5f5f,  # 5
	0x5f5f87, 0x5f5faf, 0x5f5fd7, 0x5f5fff, 0x5f8700, 0x5f875f, 0x5f8787, 0x5f87af, 0x5f87d7, 0x5f87ff,  # 6
	0x5faf00, 0x5faf5f, 0x5faf87, 0x5fafaf, 0x5fafd7, 0x5fafff, 0x5fd700, 0x5fd75f, 0x5fd787, 0x5fd7af,  # 7
	0x5fd7d7, 0x5fd7ff, 0x5fff00, 0x5fff5f, 0x5fff87, 0x5fffaf, 0x5fffd7, 0x5fffff, 0x870000, 0x87005f,  # 8
	0x870087, 0x8700af, 0x8700d7, 0x8700ff, 0x875f00, 0x875f5f, 0x875f87, 0x875faf, 0x875fd7, 0x875fff,  # 9
	0x878700, 0x87875f, 0x878787, 0x8787af, 0x8787d7, 0x8787ff, 0x87af00, 0x87af5f, 0x87af87, 0x87afaf,  # 10
	0x87afd7, 0x87afff, 0x87d700, 0x87d75f, 0x87d787, 0x87d7af, 0x87d7d7, 0x87d7ff, 0x87ff00, 0x87ff5f,  # 11
	0x87ff87, 0x87ffaf, 0x87ffd7, 0x87ffff, 0xaf0000, 0xaf005f, 0xaf0087, 0xaf00af, 0xaf00d7, 0xaf00ff,  # 12
	0xaf5f00, 0xaf5f5f, 0xaf5f87, 0xaf5faf, 0xaf5fd7, 0xaf5fff, 0xaf8700, 0xaf875f, 0xaf8787, 0xaf87af,  # 13
	0xaf87d7, 0xaf87ff, 0xafaf00, 0xafaf5f, 0xafaf87, 0xafafaf, 0xafafd7, 0xafafff, 0xafd700, 0xafd75f,  # 14
	0xafd787, 0xafd7af, 0xafd7d7, 0xafd7ff, 0xafff00, 0xafff5f, 0xafff87, 0xafffaf, 0xafffd7, 0xafffff,  # 15
	0xd70000, 0xd7005f, 0xd70087, 0xd700af, 0xd700d7, 0xd700ff, 0xd75f00, 0xd75f5f, 0xd75f87, 0xd75faf,  # 16
	0xd75fd7, 0xd75fff, 0xd78700, 0xd7875f, 0xd78787, 0xd787af, 0xd787d7, 0xd787ff, 0xd7af00, 0xd7af5f,  # 17
	0xd7af87, 0xd7afaf, 0xd7afd7, 0xd7afff, 0xd7d700, 0xd7d75f, 0xd7d787, 0xd7d7af, 0xd7d7d7, 0xd7d7ff,  # 18
	0xd7ff00, 0xd7ff5f, 0xd7ff87, 0xd7ffaf, 0xd7ffd7, 0xd7ffff, 0xff0000, 0xff005f, 0xff0087, 0xff00af,  # 19
	0xff00d7, 0xff00ff, 0xff5f00, 0xff5f5f, 0xff5f87, 0xff5faf, 0xff5fd7, 0xff5fff, 0xff8700, 0xff875f,  # 20
	0xff8787, 0xff87af, 0xff87d7, 0xff87ff, 0xffaf00, 0xffaf5f, 0xffaf87, 0xffafaf, 0xffafd7, 0xffafff,  # 21
	0xffd700, 0xffd75f, 0xffd787, 0xffd7af, 0xffd7d7, 0xffd7ff, 0xffff00, 0xffff5f, 0xffff87, 0xffffaf,  # 22
	0xffffd7, 0xffffff, 0x080808, 0x121212, 0x1c1c1c, 0x262626, 0x303030, 0x3a3a3a, 0x444444, 0x4e4e4e,  # 23
	0x585858, 0x626262, 0x6c6c6c, 0x767676, 0x808080, 0x8a8a8a, 0x949494, 0x9e9e9e, 0xa8a8a8, 0xb2b2b2,  # 24
	0xbcbcbc, 0xc6c6c6, 0xd0d0d0, 0xdadada, 0xe4e4e4, 0xeeeeee                                           # 25
)
