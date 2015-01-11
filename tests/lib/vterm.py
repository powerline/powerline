# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import ctypes

from powerline.lib.unicode import unicode, unichr, tointiter


class CTypesFunction(object):
	def __init__(self, library, name, rettype, args):
		self.name = name
		self.prototype = ctypes.CFUNCTYPE(rettype, *[
			arg[1] for arg in args
		])
		self.args = args
		self.func = self.prototype((name, library), tuple((
			(1, arg[0]) for arg in args
		)))

	def __call__(self, *args, **kwargs):
		return self.func(*args, **kwargs)

	def __repr__(self):
		return '{cls}(<library>, {name!r}, {rettype!r}, {args!r})'.format(
			cls=self.__class__.__name__,
			**self.__dict__
		)


class CTypesLibraryFuncsCollection(object):
	def __init__(self, lib, **kwargs):
		self.lib = lib
		library_loader = ctypes.LibraryLoader(ctypes.CDLL)
		library = library_loader.LoadLibrary(lib)
		self.library = library
		for name, args in kwargs.items():
			self.__dict__[name] = CTypesFunction(library, name, *args)


class VTermPos_s(ctypes.Structure):
	_fields_ = (
		('row', ctypes.c_int),
		('col', ctypes.c_int),
	)


class VTermColor_s(ctypes.Structure):
	_fields_ = (
		('red', ctypes.c_uint8),
		('green', ctypes.c_uint8),
		('blue', ctypes.c_uint8),
	)


class VTermScreenCellAttrs_s(ctypes.Structure):
	_fields_ = (
		('bold', ctypes.c_uint, 1),
		('underline', ctypes.c_uint, 2),
		('italic', ctypes.c_uint, 1),
		('blink', ctypes.c_uint, 1),
		('reverse', ctypes.c_uint, 1),
		('strike', ctypes.c_uint, 1),
		('font', ctypes.c_uint, 4),
		('dwl', ctypes.c_uint, 1),
		('dhl', ctypes.c_uint, 2),
	)


VTERM_MAX_CHARS_PER_CELL = 6


class VTermScreenCell_s(ctypes.Structure):
	_fields_ = (
		('chars', ctypes.ARRAY(ctypes.c_uint32, VTERM_MAX_CHARS_PER_CELL)),
		('width', ctypes.c_char),
		('attrs', VTermScreenCellAttrs_s),
		('fg', VTermColor_s),
		('bg', VTermColor_s),
	)


VTerm_p = ctypes.c_void_p
VTermScreen_p = ctypes.c_void_p


def get_functions(lib):
	return CTypesLibraryFuncsCollection(
		lib,
		vterm_new=(VTerm_p, (
			('rows', ctypes.c_int),
			('cols', ctypes.c_int)
		)),
		vterm_obtain_screen=(VTermScreen_p, (('vt', VTerm_p),)),
		vterm_screen_reset=(None, (
			('screen', VTermScreen_p),
			('hard', ctypes.c_int)
		)),
		vterm_input_write=(ctypes.c_size_t, (
			('vt', VTerm_p),
			('bytes', ctypes.POINTER(ctypes.c_char)),
			('size', ctypes.c_size_t),
		)),
		vterm_screen_get_cell=(ctypes.c_int, (
			('screen', VTermScreen_p),
			('pos', VTermPos_s),
			('cell', ctypes.POINTER(VTermScreenCell_s))
		)),
		vterm_free=(None, (('vt', VTerm_p),)),
	)


class VTermColor(object):
	__slots__ = ('red', 'green', 'blue')

	def __init__(self, color):
		self.red = color.red
		self.green = color.green
		self.blue = color.blue

	@property
	def color_key(self):
		return (self.red, self.green, self.blue)


class VTermScreenCell(object):
	def __init__(self, vtsc):
		for field in VTermScreenCellAttrs_s._fields_:
			field_name = field[0]
			setattr(self, field_name, getattr(vtsc.attrs, field_name))
		self.text = ''.join((
			unichr(vtsc.chars[i]) for i in range(VTERM_MAX_CHARS_PER_CELL)
		)).rstrip('\x00')
		self.width = next(tointiter(vtsc.width))
		self.fg = VTermColor(vtsc.fg)
		self.bg = VTermColor(vtsc.bg)
		self.cell_properties_key = (
			self.fg.color_key,
			self.bg.color_key,
			self.bold,
			self.underline,
			self.italic,
		)


class VTermScreen(object):
	def __init__(self, functions, screen):
		self.functions = functions
		self.screen = screen

	def __getitem__(self, position):
		pos = VTermPos_s(*position)
		cell = VTermScreenCell_s()
		ret = self.functions.vterm_screen_get_cell(self.screen, pos, cell)
		if ret != 1:
			raise ValueError('vterm_screen_get_cell returned {0}'.format(ret))
		return VTermScreenCell(cell)

	def reset(self, hard):
		self.functions.vterm_screen_reset(self.screen, int(bool(hard)))


class VTerm(object):
	def __init__(self, lib, rows, cols):
		self.functions = get_functions(lib)
		self.vt = self.functions.vterm_new(rows, cols)
		self.vtscreen = VTermScreen(self.functions, self.functions.vterm_obtain_screen(self.vt))
		self.vtscreen.reset(True)

	def push(self, data):
		if isinstance(data, unicode):
			data = data.encode('utf-8')
		return self.functions.vterm_input_write(self.vt, data, len(data))

	def __del__(self):
		try:
			self.functions.vterm_free(self.vt)
		except AttributeError:
			pass
