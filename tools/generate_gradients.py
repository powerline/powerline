#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
'''Gradients generator
'''
from __future__ import division
import sys
import json
from powerline.colorscheme import cterm_to_hex
from itertools import groupby
import argparse

try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


def num2(s):
	try:
		return (True, [int(v) for v in s.partition(' ')[::2]])
	except TypeError:
		return (False, [float(v) for v in s.partition(' ')[::2]])


def rgbint_to_rgb(rgbint):
	return ((rgbint >> 16) & 0xFF, (rgbint >> 8) & 0xFF, rgbint & 0xFF)


def color(s):
	if len(s) <= 3:
		return rgbint_to_rgb(cterm_to_hex[int(s)])
	else:
		return rgbint_to_rgb(int(s, 16))


def nums(s):
	return [int(i) for i in s.split()]


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('gradient', nargs='*', metavar='COLOR', type=color, help='List of colors (either indexes from 8-bit palette or 24-bit RGB in hexadecimal notation)')
p.add_argument('-n', '--num_items', metavar='INT', type=int, help='Number of items in resulting list', default=101)
p.add_argument('-N', '--num_output', metavar='INT', type=int, help='Number of characters in sample', default=101)
p.add_argument('-r', '--range', metavar='V1 V2', type=num2, help='Use this range when outputting scale')
p.add_argument('-s', '--show', action='store_true', help='If present output gradient sample')
p.add_argument('-p', '--palette', choices=('16', '256'), help='Use this palette. Defaults to 240-color palette (256 colors without first 16)')
p.add_argument('-w', '--weights', metavar='INT INT ...', type=nums, help='Adjust weights of colors. Number of weights must be equal to number of colors')

args = p.parse_args()


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


def get_rgb(*args):
	return "%02x%02x%02x" % args


def col_distance(rgb1, rgb2):
	return sum(((rgb1[i] - rgb2[i]) ** 2 for i in range(3)))


def find_color(urgb, colors, ctrans):
	cur_distance = 3 * (255 ** 2 + 1)
	cur_color = None
	i = 0
	for crgbint in colors:
		crgb = rgbint_to_rgb(crgbint)
		dist = col_distance(urgb, crgb)
		if dist < cur_distance:
			cur_distance = dist
			cur_color = (ctrans(i), crgb)
		i += 1
	return cur_color


def print_color(color):
	if type(color) is int:
		colstr = '5;' + str(color)
	else:
		colstr = '2;' + ';'.join((str(int(round(i))) for i in color))
	sys.stdout.write('\033[48;' + colstr + 'm ')


def print_colors(colors, num):
	for i in range(num):
		color = colors[int(round(i * (len(colors) - 1) / num))]
		print_color(color)
	sys.stdout.write('\033[0m\n')


def dec_scale_generator(num):
	j = 0
	r = ''
	while num:
		r += '\033[{0}m'.format(j % 2)
		for i in range(10):
			r += str(i)
			num -= 1
			if not num:
				break
		j += 1
	r += '\033[0m\n'
	return r


m = args.num_items

maxweight = len(args.gradient) - 1
if args.weights:
	weight_sum = sum(args.weights)
	norm_weights = [100.0 * weight / weight_sum for weight in args.weights]
	steps = [0]
	for weight in norm_weights:
		steps.append(steps[-1] + weight)
	steps.pop(0)
	steps.pop(0)
else:
	step = m / maxweight
	steps = [i * step for i in range(1, maxweight + 1)]

data = [(weight, args.gradient[i - 1], args.gradient[i]) for weight, i in zip(steps, range(1, len(args.gradient)))]
gr_func = gradient(data)
gradient = [gr_func(y) for y in range(0, m)]
palettes = {
	'16': (cterm_to_hex[:16], lambda c: c),
	'256': (cterm_to_hex, lambda c: c),
	None: (cterm_to_hex[16:], lambda c: c + 16),
}
r = [get_rgb(*color) for color in gradient]
r2 = [find_color(color, *palettes[args.palette])[0] for color in gradient]
r3 = [i[0] for i in groupby(r2)]
print(json.dumps(r))
print(json.dumps(r2))
print(json.dumps(r3))
if args.show:
	print_colors(args.gradient, args.num_output)
	print_colors(gradient, args.num_output)
	print_colors(r2, args.num_output)
	print_colors(r3, args.num_output)
	if not args.range and args.num_output >= 32 and (args.num_output - 1) // 10 >= 4 and (args.num_output - 1) % 10 == 0:
		sys.stdout.write('0')
		sys.stdout.write(''.join(('%*u' % (args.num_output // 10, i) for i in range(10, 101, 10))))
		sys.stdout.write('\n')
	else:
		if args.range:
			vmin, vmax = args.range[1]
			isint = args.range[0]
		else:
			isint = True
			vmin = 0
			vmax = 100
		s = ''
		lasts = ' ' + str(vmax)
		while len(s) + len(lasts) < args.num_output:
			curpc = len(s) + 1 if s else 0
			curval = vmin + curpc * (vmax - vmin) / args.num_output
			if isint:
				curval = int(round(curval))
			s += str(curval) + ' '
		sys.stdout.write(s[:-1] + lasts + '\n')
	sys.stdout.write(dec_scale_generator(args.num_output) + '\n')
