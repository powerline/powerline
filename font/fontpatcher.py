#!/usr/bin/env python2
# vim:fileencoding=utf-8:noet

import argparse
import sys
import re
import os.path

try:
	import fontforge
	import psMat
except ImportError:
	sys.stderr.write('The required FontForge modules could not be loaded.\n\n')
	if sys.version_info.major > 2:
		sys.stderr.write('FontForge only supports Python 2. Please run this script with the Python 2 executable - e.g. "python2 {0}"\n'.format(sys.argv[0]))
	else:
		sys.stderr.write('You need FontForge with Python bindings for this script to work.\n')
	sys.exit(1)

# Handle command-line arguments
parser = argparse.ArgumentParser(description='Font patcher for Powerline. Requires FontForge with Python bindings. Stores the patched font as a new, renamed font file by default.')
parser.add_argument('target_fonts', help='font files to patch', metavar='font', nargs='+', type=argparse.FileType('rb'))
parser.add_argument('--no-rename', help='don\'t add " for Powerline" to the font name', default=True, action='store_false', dest='rename_font')
parser.add_argument('--source-font', help='source symbol font', metavar='font', dest='source_font', default='{0}/fontpatcher-symbols.sfd'.format(sys.path[0]), type=argparse.FileType('rb'))
args = parser.parse_args()


class FontPatcher(object):
	def __init__(self, source_font, target_fonts, rename_font=True):
		self.source_font = fontforge.open(source_font.name)
		self.target_fonts = (fontforge.open(target_font.name) for target_font in target_fonts)
		self.rename_font = rename_font

	def patch(self):
		for target_font in self.target_fonts:
			source_font = self.source_font
			target_font_em_original = target_font.em
			target_font.em = 2048
			target_font.encoding = 'ISO10646'

			# Rename font
			if self.rename_font:
				target_font.familyname += ' for Powerline'
				target_font.fullname += ' for Powerline'
				fontname, style = re.match("^([^-]*)(?:(-.*))?$", target_font.fontname).groups()
				target_font.fontname = fontname + 'ForPowerline'
				if style is not None:
					target_font.fontname += style
				target_font.appendSFNTName('English (US)', 'Preferred Family', target_font.familyname)
				target_font.appendSFNTName('English (US)', 'Compatible Full', target_font.fullname)

			source_bb = source_font['block'].boundingBox()
			target_bb = [0, 0, 0, 0]
			target_font_width = 0

			# Find the biggest char width and height in the Latin-1 extended range and the box drawing range
			# This isn't ideal, but it works fairly well - some fonts may need tuning after patching
			for cp in range(0x00, 0x17f) + range(0x2500, 0x2600):
				try:
					bbox = target_font[cp].boundingBox()
				except TypeError:
					continue
				if not target_font_width:
					target_font_width = target_font[cp].width
				if bbox[0] < target_bb[0]:
					target_bb[0] = bbox[0]
				if bbox[1] < target_bb[1]:
					target_bb[1] = bbox[1]
				if bbox[2] > target_bb[2]:
					target_bb[2] = bbox[2]
				if bbox[3] > target_bb[3]:
					target_bb[3] = bbox[3]

			# Find source and target size difference for scaling
			x_ratio = (target_bb[2] - target_bb[0]) / (source_bb[2] - source_bb[0])
			y_ratio = (target_bb[3] - target_bb[1]) / (source_bb[3] - source_bb[1])
			scale = psMat.scale(x_ratio, y_ratio)

			# Find source and target midpoints for translating
			x_diff = target_bb[0] - source_bb[0]
			y_diff = target_bb[1] - source_bb[1]
			translate = psMat.translate(x_diff, y_diff)
			transform = psMat.compose(scale, translate)

			# Create new glyphs from symbol font
			for source_glyph in source_font.glyphs():
				if source_glyph == source_font['block']:
					# Skip the symbol font block glyph
					continue

				# Select and copy symbol from its encoding point
				source_font.selection.select(source_glyph.encoding)
				source_font.copy()

				# Select and paste symbol to its unicode code point
				target_font.selection.select(source_glyph.unicode)
				target_font.paste()

				# Transform the glyph
				target_font.transform(transform)

				# Reset the font's glyph width so it's still considered monospaced
				target_font[source_glyph.unicode].width = target_font_width

			target_font.em = target_font_em_original

			# Generate patched font
			extension = os.path.splitext(target_font.path)[1]
			if extension.lower() not in ['.ttf', '.otf']:
				# Default to OpenType if input is not TrueType/OpenType
				extension = '.otf'
			target_font.generate('{0}{1}'.format(target_font.fullname, extension))

fp = FontPatcher(args.source_font, args.target_fonts, args.rename_font)
fp.patch()
