#!/usr/bin/env python
import sys
import os


def get_color(name, rgb):
	return name, (int(rgb[:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16))


with open(os.path.join(os.path.dirname(__file__), 'colors.map'), 'r') as f:
	colors = [get_color(*line.split('\t')) for line in f]


urgb = get_color(None, sys.argv[1])[1]


def col_distance(rgb1, rgb2):
	return sum(((rgb1[i] - rgb2[i]) ** 2 for i in range(3)))


def find_color(urgb, colors):
	cur_distance = 3 * (255 ** 2 + 1)
	cur_color = None
	for color, crgb in colors:
		dist = col_distance(urgb, crgb)
		if dist < cur_distance:
			cur_distance = dist
			cur_color = (color, crgb)
	return cur_color


cur_color = find_color(urgb, colors)

print urgb, ':', cur_color

col_1 = ';2;' + ';'.join((str(i) for i in urgb)) + 'm'
col_2 = ';2;' + ';'.join((str(i) for i in cur_color[1])) + 'm'
sys.stdout.write('\033[48' + col_1 + '\033[38' + col_2 + 'abc\033[0m <-- bg:urgb, fg:crgb\n')
sys.stdout.write('\033[48' + col_2 + '\033[38' + col_1 + 'abc\033[0m <-- bg:crgb, fg:urgb\n')
