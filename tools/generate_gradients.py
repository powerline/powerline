#!/usr/bin/env python
import sys
import json
from powerline.colorscheme import cterm_to_hex
from itertools import groupby

try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


if len(sys.argv) == 1 or sys.argv[1] == '--help':
	sys.stderr.write('''
	Usage: generate_gradients.py colors itemnum[ "show" [ min max num]]

		colors: JSON list with either cterm ([200, 42, 6]) or RGB (["abcdef", 
			"feffef"]) colors.

		itemnum: number of items in generated gradient.

		"show": static string, determines whether gradient sample should be 
			printed to stdout as well.

		min, max: floating point values.
		num: integer

				all of the above are used to generate sample gradient for given 
				range (just like the above gradients shown with "show", but with 
				different scale (controlled by min and max) and, possibly, 
				different length (controlled by num)).
	''')
	sys.exit(1)


def linear_gradient(start_value, stop_value, start_offset, stop_offset, offset):
	return start_value + ((offset - start_offset) * (stop_value - start_value) / (stop_offset - start_offset))


def gradient(DATA):
	def gradient_function(y):
		initial_offset = 0
		for offset, start, end in DATA:
			if y <= offset:
				return [linear_gradient(start[i], end[i], initial_offset, offset, y) for i in range(3)]
			initial_offset = offset
	return gradient_function


def get_color(rgb):
	if type(rgb) is unicode:
		return int(rgb[:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
	else:
		return rgbint_to_rgb(cterm_to_hex[rgb])


def get_rgb(*args):
	return "%02x%02x%02x" % args


def col_distance(rgb1, rgb2):
	return sum(((rgb1[i] - rgb2[i]) ** 2 for i in range(3)))


def rgbint_to_rgb(rgbint):
	return ((rgbint >> 16) & 0xFF, (rgbint >> 8) & 0xFF, rgbint & 0xFF)


def find_color(urgb, colors):
	cur_distance = 3 * (255 ** 2 + 1)
	cur_color = None
	i = 0
	for crgbint in colors:
		crgb = rgbint_to_rgb(crgbint)
		dist = col_distance(urgb, crgb)
		if dist < cur_distance:
			cur_distance = dist
			cur_color = (i, crgb)
		i += 1
	return cur_color


def print_color(color):
	if type(color) is int:
		colstr = '5;' + str(color)
	else:
		colstr = '2;' + ';'.join((str(int(round(i))) for i in color))
	sys.stdout.write('\033[48;' + colstr + 'm ')


def print_colors(colors, num=100):
	for i in range(num + 1):
		color = colors[int(round(i * (len(colors) - 1) / num))]
		print_color(color)
	sys.stdout.write('\033[0m\n')


c = [get_color(color) for color in json.loads(sys.argv[1])]
m = int(sys.argv[2]) if len(sys.argv) > 2 else 100
m += m % (len(c) - 1)
step = m / (len(c) - 1)
data = [(i * step, c[i - 1], c[i]) for i in range(1, len(c))]
gr_func = gradient(data)
gradient = [gr_func(y) for y in range(0, m - 1)]
r = [get_rgb(*color) for color in gradient]
r2 = [find_color(color, cterm_to_hex)[0] for color in gradient]
r3 = [i[0] for i in groupby(r2)]
print(json.dumps(r))
print(json.dumps(r2))
print(json.dumps(r3))
if len(sys.argv) > 3 and sys.argv[3] == 'show':
	print_colors(gradient)
	print_colors(r2)
	print_colors(r3)
	sys.stdout.write('0')
	sys.stdout.write(''.join(('%10u' % (i * 10) for i in range(1, 11))))
	sys.stdout.write('\n')
	nums = (''.join((str(i) for i in range(10))))
	sys.stdout.write(''.join(((('\033[1m' if j % 2 else '\033[0m') + nums) for j in range(10))))
	sys.stdout.write('\033[0m0\n')
	if len(sys.argv) > 6:
		vmin = float(sys.argv[4])
		vmax = float(sys.argv[5])
		num = int(sys.argv[6])
		print_colors(gradient, num)
		s = ''
		while len(s) < num:
			curpc = len(s) + 1 if s else 0
			curval = vmin + curpc * (vmax - vmin) / 100.0
			s += str(curval) + ' '
		print(s)
