#!/usr/bin/env python
# vim:fileencoding=utf-8:noet

'''Gradients generator
'''

from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import json
import argparse

from itertools import groupby

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

from powerline.colorscheme import cterm_to_hex


def num2(s):
	try:
		return (True, [int(v) for v in s.partition(' ')[::2]])
	except TypeError:
		return (False, [float(v) for v in s.partition(' ')[::2]])


def rgbint_to_lab(rgbint):
	rgb = sRGBColor(
		(rgbint >> 16) & 0xFF, (rgbint >> 8) & 0xFF, rgbint & 0xFF,
		is_upscaled=True
	)
	return convert_color(rgb, LabColor)


cterm_to_lab = tuple((rgbint_to_lab(v) for v in cterm_to_hex))


def color(s):
	if len(s) <= 3:
		return cterm_to_lab[int(s)]
	else:
		return rgbint_to_lab(int(s, 16))


def nums(s):
	return [int(i) for i in s.split()]


def linear_gradient(start_value, stop_value, start_offset, stop_offset, offset):
	return start_value + ((offset - start_offset) * (stop_value - start_value) / (stop_offset - start_offset))


def lab_gradient(slab, elab, soff, eoff, off):
	svals = slab.get_value_tuple()
	evals = elab.get_value_tuple()
	return LabColor(*[
		linear_gradient(start_value, end_value, soff, eoff, off)
		for start_value, end_value in zip(svals, evals)
	])


def generate_gradient_function(DATA):
	def gradient_function(y):
		initial_offset = 0
		for offset, start, end in DATA:
			if y <= offset:
				return lab_gradient(start, end, initial_offset, offset, y)
			initial_offset = offset
	return gradient_function


def get_upscaled_values(rgb):
	return [min(max(0, i), 255) for i in rgb.get_upscaled_value_tuple()]


def get_rgb(lab):
	rgb = convert_color(lab, sRGBColor)
	rgb = sRGBColor(*get_upscaled_values(rgb), is_upscaled=True)
	return rgb.get_rgb_hex()[1:]


def find_color(ulab, colors, ctrans):
	cur_distance = float('inf')
	cur_color = None
	i = 0
	for clab in colors:
		dist = delta_e_cie2000(ulab, clab)
		if dist < cur_distance:
			cur_distance = dist
			cur_color = (ctrans(i), clab)
		i += 1
	return cur_color


def print_color(color):
	if type(color) is int:
		colstr = '5;' + str(color)
	else:
		rgb = convert_color(color, sRGBColor)
		colstr = '2;' + ';'.join((str(i) for i in get_upscaled_values(rgb)))
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


def compute_steps(gradient, weights):
	maxweight = len(gradient) - 1
	if weights:
		weight_sum = sum(weights)
		norm_weights = [100.0 * weight / weight_sum for weight in weights]
		steps = [0]
		for weight in norm_weights:
			steps.append(steps[-1] + weight)
		steps.pop(0)
		steps.pop(0)
	else:
		step = m / maxweight
		steps = [i * step for i in range(1, maxweight + 1)]
	return steps


palettes = {
	'16': (cterm_to_lab[:16], lambda c: c),
	'256': (cterm_to_lab, lambda c: c),
	None: (cterm_to_lab[16:], lambda c: c + 16),
}


def show_scale(rng, num_output):
	if not rng and num_output >= 32 and (num_output - 1) // 10 >= 4 and (num_output - 1) % 10 == 0:
		sys.stdout.write('0')
		sys.stdout.write(''.join(('%*u' % (num_output // 10, i) for i in range(10, 101, 10))))
		sys.stdout.write('\n')
	else:
		if rng:
			vmin, vmax = rng[1]
			isint = rng[0]
		else:
			isint = True
			vmin = 0
			vmax = 100
		s = ''
		lasts = ' ' + str(vmax)
		while len(s) + len(lasts) < num_output:
			curpc = len(s) + 1 if s else 0
			curval = vmin + curpc * (vmax - vmin) / num_output
			if isint:
				curval = int(round(curval))
			s += str(curval) + ' '
		sys.stdout.write(s[:-1] + lasts + '\n')
	sys.stdout.write(dec_scale_generator(num_output) + '\n')


if __name__ == '__main__':
	p = argparse.ArgumentParser(description=__doc__)
	p.add_argument('gradient', nargs='*', metavar='COLOR', type=color, help='List of colors (either indexes from 8-bit palette or 24-bit RGB in hexadecimal notation)')
	p.add_argument('-n', '--num_items', metavar='INT', type=int, help='Number of items in resulting list', default=101)
	p.add_argument('-N', '--num_output', metavar='INT', type=int, help='Number of characters in sample', default=101)
	p.add_argument('-r', '--range', metavar='V1 V2', type=num2, help='Use this range when outputting scale')
	p.add_argument('-s', '--show', action='store_true', help='If present output gradient sample')
	p.add_argument('-p', '--palette', choices=('16', '256'), help='Use this palette. Defaults to 240-color palette (256 colors without first 16)')
	p.add_argument('-w', '--weights', metavar='INT INT ...', type=nums, help='Adjust weights of colors. Number of weights must be equal to number of colors')
	p.add_argument('-C', '--omit-terminal', action='store_true', help='If present do not compute values for terminal')

	args = p.parse_args()

	m = args.num_items

	steps = compute_steps(args.gradient, args.weights)

	data = [
		(weight, args.gradient[i - 1], args.gradient[i])
		for weight, i in zip(steps, range(1, len(args.gradient)))
	]
	gr_func = generate_gradient_function(data)
	gradient = [gr_func(y) for y in range(0, m)]

	r = [get_rgb(lab) for lab in gradient]
	if not args.omit_terminal:
		r2 = [find_color(lab, *palettes[args.palette])[0] for lab in gradient]
		r3 = [i[0] for i in groupby(r2)]

	if not args.omit_terminal:
		print(json.dumps(r3) + ',')
		print(json.dumps(r2) + ',')
	print(json.dumps(r))

	if args.show:
		print_colors(args.gradient, args.num_output)
		if not args.omit_terminal:
			print_colors(r3, args.num_output)
			print_colors(r2, args.num_output)
		print_colors(gradient, args.num_output)

		show_scale(args.range, args.num_output)
