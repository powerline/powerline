__all__ = ['gen_marked_value', 'MarkedValue']


class MarkedValue:
	def __init__(self, value, mark):
		self.mark = mark
		self.value = value


classcache = {}


def gen_marked_value(value, mark):
	if value.__class__ in classcache:
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
