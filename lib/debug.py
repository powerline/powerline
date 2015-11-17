# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import gc
import sys

from types import FrameType
from itertools import chain


# From http://code.activestate.com/recipes/523004-find-cyclical-references/
def print_cycles(objects, outstream=sys.stdout, show_progress=False):
	'''Find reference cycles

	:param list objects:
		A list of objects to find cycles in.  It is often useful to pass in 
		gc.garbage to find the cycles that are preventing some objects from 
		being garbage collected.
	:param file outstream:
		The stream for output.
	:param bool show_progress:
		If True, print the number of objects reached as they are found.
	'''
	def print_path(path):
		for i, step in enumerate(path):
			# next “wraps around”
			next = path[(i + 1) % len(path)]

			outstream.write('	%s -- ' % str(type(step)))
			written = False
			if isinstance(step, dict):
				for key, val in step.items():
					if val is next:
						outstream.write('[%s]' % repr(key))
						written = True
						break
					if key is next:
						outstream.write('[key] = %s' % repr(val))
						written = True
						break
			elif isinstance(step, (list, tuple)):
				for i, item in enumerate(step):
					if item is next:
						outstream.write('[%d]' % i)
						written = True
			elif getattr(type(step), '__getattribute__', None) in (object.__getattribute__, type.__getattribute__):
				for attr in chain(dir(step), getattr(step, '__dict__', ())):
					if getattr(step, attr, None) is next:
						try:
							outstream.write('%r.%s' % (step, attr))
						except TypeError:
							outstream.write('.%s' % (step, attr))
						written = True
						break
			if not written:
				outstream.write(repr(step))
			outstream.write(' ->\n')
		outstream.write('\n')

	def recurse(obj, start, all, current_path):
		if show_progress:
			outstream.write('%d\r' % len(all))

		all[id(obj)] = None

		referents = gc.get_referents(obj)
		for referent in referents:
			# If we’ve found our way back to the start, this is
			# a cycle, so print it out
			if referent is start:
				try:
					outstream.write('Cyclic reference: %r\n' % referent)
				except TypeError:
					try:
						outstream.write('Cyclic reference: %i (%r)\n' % (id(referent), type(referent)))
					except TypeError:
						outstream.write('Cyclic reference: %i\n' % id(referent))
				print_path(current_path)

			# Don’t go back through the original list of objects, or
			# through temporary references to the object, since those
			# are just an artifact of the cycle detector itself.
			elif referent is objects or isinstance(referent, FrameType): 
				continue

			# We haven’t seen this object before, so recurse
			elif id(referent) not in all:
				recurse(referent, start, all, current_path + (obj,))

	for obj in objects:
		# We are not interested in non-powerline cyclic references
		try:
			if not type(obj).__module__.startswith('powerline'):
				continue
		except AttributeError:
			continue
		recurse(obj, obj, {}, ())
