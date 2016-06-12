# vim:fileencoding=utf-8:noet
def nop(_):
	pass


class Foo(object):
	def __init__(self):
		nop('__init__')
		self.bar()
		self.baz()
		self.bra()

	@classmethod
	def bar(cls):
		nop(cls.__name__)

	@staticmethod
	def baz():
		nop(1)

	def bra(self):
		nop(self.__class__.__name__)


def brah():
	nop('brah')


f = Foo()
Foo.bar()
Foo.baz()
Foo.bra(f)

f.bar()
f.baz()
f.bra()

brah()
