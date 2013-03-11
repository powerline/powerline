__all__ = ['BaseConstructor', 'Constructor', 'ConstructorError']

from .error import MarkedError
from .nodes import *  # NOQA
from .markedvalue import gen_marked_value

import collections
import types

from functools import wraps


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


def marked(func):
	@wraps(func)
	def f(self, node, *args, **kwargs):
		return gen_marked_value(func(self, node, *args, **kwargs), node.start_mark)
	return f


class ConstructorError(MarkedError):
	pass


class BaseConstructor:
	yaml_constructors = {}

	def __init__(self):
		self.constructed_objects = {}
		self.state_generators = []
		self.deep_construct = False

	def check_data(self):
		# If there are more documents available?
		return self.check_node()

	def get_data(self):
		# Construct and return the next document.
		if self.check_node():
			return self.construct_document(self.get_node())

	def get_single_data(self):
		# Ensure that the stream contains a single document and construct it.
		node = self.get_single_node()
		if node is not None:
			return self.construct_document(node)
		return None

	def construct_document(self, node):
		data = self.construct_object(node)
		while self.state_generators:
			state_generators = self.state_generators
			self.state_generators = []
			for generator in state_generators:
				for dummy in generator:
					pass
		self.constructed_objects = {}
		self.deep_construct = False
		return data

	def construct_object(self, node, deep=False):
		if node in self.constructed_objects:
			return self.constructed_objects[node]
		if deep:
			old_deep = self.deep_construct
			self.deep_construct = True
		constructor = None
		tag_suffix = None
		if node.tag in self.yaml_constructors:
			constructor = self.yaml_constructors[node.tag]
		else:
			raise ConstructorError(None, None, 'no constructor for tag %s' % node.tag)
		if tag_suffix is None:
			data = constructor(self, node)
		else:
			data = constructor(self, tag_suffix, node)
		if isinstance(data, types.GeneratorType):
			generator = data
			data = next(generator)
			if self.deep_construct:
				for dummy in generator:
					pass
			else:
				self.state_generators.append(generator)
		self.constructed_objects[node] = data
		if deep:
			self.deep_construct = old_deep
		return data

	@marked
	def construct_scalar(self, node):
		if not isinstance(node, ScalarNode):
			raise ConstructorError(None, None,
					"expected a scalar node, but found %s" % node.id,
					node.start_mark)
		return node.value

	def construct_sequence(self, node, deep=False):
		if not isinstance(node, SequenceNode):
			raise ConstructorError(None, None,
					"expected a sequence node, but found %s" % node.id,
					node.start_mark)
		return [self.construct_object(child, deep=deep)
				for child in node.value]

	@marked
	def construct_mapping(self, node, deep=False):
		if not isinstance(node, MappingNode):
			raise ConstructorError(None, None,
					"expected a mapping node, but found %s" % node.id,
					node.start_mark)
		mapping = {}
		for key_node, value_node in node.value:
			key = self.construct_object(key_node, deep=deep)
			if not isinstance(key, collections.Hashable):
				self.echoerr('While constructing a mapping', node.start_mark,
						'found unhashable key', key_node.start_mark)
				continue
			elif type(key.value) != unicode:
				self.echoerr('Error while constructing a mapping', node.start_mark,
						'found key that is not a string', key_node.start_mark)
				continue
			elif key in mapping:
				self.echoerr('Error while constructing a mapping', node.start_mark,
						'found duplicate key', key_node.start_mark)
				continue
			value = self.construct_object(value_node, deep=deep)
			mapping[key] = value
		return mapping

	@classmethod
	def add_constructor(cls, tag, constructor):
		if not 'yaml_constructors' in cls.__dict__:
			cls.yaml_constructors = cls.yaml_constructors.copy()
		cls.yaml_constructors[tag] = constructor


class Constructor(BaseConstructor):
	def construct_scalar(self, node):
		if isinstance(node, MappingNode):
			for key_node, value_node in node.value:
				if key_node.tag == 'tag:yaml.org,2002:value':
					return self.construct_scalar(value_node)
		return BaseConstructor.construct_scalar(self, node)

	def flatten_mapping(self, node):
		merge = []
		index = 0
		while index < len(node.value):
			key_node, value_node = node.value[index]
			if key_node.tag == 'tag:yaml.org,2002:merge':
				del node.value[index]
				if isinstance(value_node, MappingNode):
					self.flatten_mapping(value_node)
					merge.extend(value_node.value)
				elif isinstance(value_node, SequenceNode):
					submerge = []
					for subnode in value_node.value:
						if not isinstance(subnode, MappingNode):
							raise ConstructorError("while constructing a mapping",
									node.start_mark,
									"expected a mapping for merging, but found %s"
									% subnode.id, subnode.start_mark)
						self.flatten_mapping(subnode)
						submerge.append(subnode.value)
					submerge.reverse()
					for value in submerge:
						merge.extend(value)
				else:
					raise ConstructorError("while constructing a mapping", node.start_mark,
							"expected a mapping or list of mappings for merging, but found %s"
							% value_node.id, value_node.start_mark)
			elif key_node.tag == 'tag:yaml.org,2002:value':
				key_node.tag = 'tag:yaml.org,2002:str'
				index += 1
			else:
				index += 1
		if merge:
			node.value = merge + node.value

	def construct_mapping(self, node, deep=False):
		if isinstance(node, MappingNode):
			self.flatten_mapping(node)
		return BaseConstructor.construct_mapping(self, node, deep=deep)

	@marked
	def construct_yaml_null(self, node):
		self.construct_scalar(node)
		return None

	@marked
	def construct_yaml_bool(self, node):
		value = self.construct_scalar(node).value
		return bool(value)

	@marked
	def construct_yaml_int(self, node):
		value = self.construct_scalar(node).value
		sign = +1
		if value[0] == '-':
			sign = -1
		if value[0] in '+-':
			value = value[1:]
		if value == '0':
			return 0
		else:
			return sign * int(value)

	@marked
	def construct_yaml_float(self, node):
		value = self.construct_scalar(node).value
		sign = +1
		if value[0] == '-':
			sign = -1
		if value[0] in '+-':
			value = value[1:]
		else:
			return sign * float(value)

	def construct_yaml_str(self, node):
		return self.construct_scalar(node)

	def construct_yaml_seq(self, node):
		data = gen_marked_value([], node.start_mark)
		yield data
		data.extend(self.construct_sequence(node))

	def construct_yaml_map(self, node):
		data = gen_marked_value({}, node.start_mark)
		yield data
		value = self.construct_mapping(node)
		data.update(value)

	def construct_undefined(self, node):
		raise ConstructorError(None, None,
				"could not determine a constructor for the tag %r" % node.tag,
				node.start_mark)


Constructor.add_constructor(
		'tag:yaml.org,2002:null',
		Constructor.construct_yaml_null)

Constructor.add_constructor(
		'tag:yaml.org,2002:bool',
		Constructor.construct_yaml_bool)

Constructor.add_constructor(
		'tag:yaml.org,2002:int',
		Constructor.construct_yaml_int)

Constructor.add_constructor(
		'tag:yaml.org,2002:float',
		Constructor.construct_yaml_float)

Constructor.add_constructor(
		'tag:yaml.org,2002:str',
		Constructor.construct_yaml_str)

Constructor.add_constructor(
		'tag:yaml.org,2002:seq',
		Constructor.construct_yaml_seq)

Constructor.add_constructor(
		'tag:yaml.org,2002:map',
		Constructor.construct_yaml_map)

Constructor.add_constructor(None,
		Constructor.construct_undefined)
