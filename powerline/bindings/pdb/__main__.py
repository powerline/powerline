#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import pdb

from powerline.bindings.pdb import use_powerline_prompt


def main():
	'''Run module as a script

	Uses :py:func:`pdb.main` function directly, but prior to that it mocks 
	:py:class:`pdb.Pdb` class with powerline-specific class instance.
	'''
	orig_pdb = pdb.Pdb

	@use_powerline_prompt
	class Pdb(pdb.Pdb, object):
		def __init__(self):
			orig_pdb.__init__(self)

	pdb.Pdb = Pdb

	return pdb.main()


if __name__ == '__main__':
	main()
