__version__ = '3.10'


from .loader import Loader


def load(stream, Loader=Loader):
	"""
	Parse the first YAML document in a stream
	and produce the corresponding Python object.
	"""
	loader = Loader(stream)
	try:
		r = loader.get_single_data()
		return r, loader.haserrors
	finally:
		loader.dispose()
