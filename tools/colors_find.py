#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000


def get_lab(name, rgb):
	rgb = sRGBColor(
		int(rgb[:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16),
		is_upscaled=True
	)
	lab = convert_color(rgb, LabColor)
	return name, lab


with open(os.path.join(os.path.dirname(__file__), 'colors.map'), 'r') as f:
	colors = [get_lab(*line.split('\t')) for line in f]


ulab = get_lab(None, sys.argv[1])[1]


def find_color(urgb, colors):
	cur_distance = 3 * (255 ** 2 + 1)
	cur_color = None
	for color, clab in colors:
		dist = delta_e_cie2000(ulab, clab)
		if dist < cur_distance:
			cur_distance = dist
			cur_color = (color, clab)
	return cur_color


cur_color = find_color(ulab, colors)


def lab_to_csi(lab):
	rgb = convert_color(lab, sRGBColor)
	colstr = ';2;' + ';'.join((str(i) for i in get_upscaled_values(rgb)))
	return colstr + 'm'


def get_upscaled_values(rgb):
	return [min(max(0, i), 255) for i in rgb.get_upscaled_value_tuple()]


def get_rgb(lab):
	rgb = convert_color(lab, sRGBColor)
	rgb = sRGBColor(*get_upscaled_values(rgb), is_upscaled=True)
	return rgb.get_rgb_hex()[1:]

print(get_rgb(ulab), ':', cur_color[0], ':', get_rgb(cur_color[1]))

col_1 = lab_to_csi(ulab)
col_2 = lab_to_csi(cur_color[1])
sys.stdout.write('\033[48' + col_1 + '\033[38' + col_2 + 'abc\033[0m <-- bg:urgb, fg:crgb\n')
sys.stdout.write('\033[48' + col_2 + '\033[38' + col_1 + 'abc\033[0m <-- bg:crgb, fg:urgb\n')
