__all__ = ['gen_marked_value', 'MarkedValue']


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str


def gen_new(cls):
	def __new__(arg_cls, value, mark):
		r = super(arg_cls, arg_cls).__new__(arg_cls, value)
		r.mark = mark
		r.value = value
		return r
	return __new__


class MarkedUnicode(unicode):
	__new__ = gen_new(unicode)

	def _proc_partition(self, part_result):
		pointdiff = 1
		r = []
		for s in part_result:
			mark = self.mark.copy()
			# XXX Does not work properly with escaped strings, but this requires 
			# saving much more information in mark.
			mark.column += pointdiff
			mark.pointer += pointdiff
			r.append(MarkedUnicode(s, mark))
			pointdiff += len(s)
		return tuple(r)

	def rpartition(self, sep):
		return self._proc_partition(super(MarkedUnicode, self).rpartition(sep))

	def partition(self, sep):
		return self._proc_partition(super(MarkedUnicode, self).partition(sep))


class MarkedInt(int):
	__new__ = gen_new(int)


class MarkedFloat(float):
	__new__ = gen_new(float)


class MarkedValue:
	def __init__(self, value, mark):
		self.mark = mark
		self.value = value


specialclasses = {
	unicode: MarkedUnicode,
	int: MarkedInt,
	float: MarkedFloat,
}

classcache = {}


def gen_marked_value(value, mark, use_special_classes=True):
	if use_special_classes and value.__class__ in specialclasses:
		Marked = specialclasses[value.__class__]
	elif value.__class__ in classcache:
		Marked = classcache[value.__class__]
	else:
		class Marked(MarkedValue):
			for func in value.__class__.__dict__:
				if func not in set(('__init__', '__new__', '__getattribute__')):
					if func in set(('__eq__',)):
						# HACK to make marked dictionaries always work
						exec (('def {0}(self, *args):\n'
								'	return self.value.{0}(*[arg.value if isinstance(arg, MarkedValue) else arg for arg in args])').format(func))
					else:
						exec (('def {0}(self, *args, **kwargs):\n'
								'	return self.value.{0}(*args, **kwargs)\n').format(func))
		classcache[value.__class__] = Marked

	return Marked(value, mark)
