# -*- coding: utf-8 -*-

from colorscheme import cterm_to_hex


def mksegment(contents=None, cterm_fg=False, cterm_bg=False, attr=False, hex_fg=False, hex_bg=False, side='l', draw_divider=True, priority=-1, filler=False):
	'''Convenience wrapper for segment generation.
	'''
	try:
		contents = unicode(contents or u'')
	except UnicodeDecodeError:
		contents = contents.decode('utf-8') or u''

	return {
		'contents': contents,
		'fg': (cterm_fg, hex_fg or cterm_to_hex.get(cterm_fg, 0xffffff)),
		'bg': (cterm_bg, hex_bg or cterm_to_hex.get(cterm_bg, 0x000000)),
		'attr': attr,
		'side': side,
		'draw_divider': False if filler else draw_divider,
		'priority': priority,
		'filler': filler,
	}
