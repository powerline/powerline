# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from powerline.lint.markedjson.error import MarkedError
from powerline.lint.markedjson import nodes


class ResolverError(MarkedError):
	pass


class BaseResolver:
	DEFAULT_SCALAR_TAG = 'tag:yaml.org,2002:str'
	DEFAULT_SEQUENCE_TAG = 'tag:yaml.org,2002:seq'
	DEFAULT_MAPPING_TAG = 'tag:yaml.org,2002:map'

	yaml_implicit_resolvers = {}
	yaml_path_resolvers = {}

	def __init__(self):
		self.resolver_exact_paths = []
		self.resolver_prefix_paths = []

	@classmethod
	def add_implicit_resolver(cls, tag, regexp, first):
		if 'yaml_implicit_resolvers' not in cls.__dict__:
			cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()
		if first is None:
			first = [None]
		for ch in first:
			cls.yaml_implicit_resolvers.setdefault(ch, []).append((tag, regexp))

	def descend_resolver(self, current_node, current_index):
		if not self.yaml_path_resolvers:
			return
		exact_paths = {}
		prefix_paths = []
		if current_node:
			depth = len(self.resolver_prefix_paths)
			for path, kind in self.resolver_prefix_paths[-1]:
				if self.check_resolver_prefix(depth, path, kind, current_node, current_index):
					if len(path) > depth:
						prefix_paths.append((path, kind))
					else:
						exact_paths[kind] = self.yaml_path_resolvers[path, kind]
		else:
			for path, kind in self.yaml_path_resolvers:
				if not path:
					exact_paths[kind] = self.yaml_path_resolvers[path, kind]
				else:
					prefix_paths.append((path, kind))
		self.resolver_exact_paths.append(exact_paths)
		self.resolver_prefix_paths.append(prefix_paths)

	def ascend_resolver(self):
		if not self.yaml_path_resolvers:
			return
		self.resolver_exact_paths.pop()
		self.resolver_prefix_paths.pop()

	def check_resolver_prefix(self, depth, path, kind, current_node, current_index):
		node_check, index_check = path[depth - 1]
		if isinstance(node_check, str):
			if current_node.tag != node_check:
				return
		elif node_check is not None:
			if not isinstance(current_node, node_check):
				return
		if index_check is True and current_index is not None:
			return
		if ((index_check is False or index_check is None)
			and current_index is None):
			return
		if isinstance(index_check, str):
			if not (isinstance(current_index, nodes.ScalarNode) and index_check == current_index.value):
				return
		elif isinstance(index_check, int) and not isinstance(index_check, bool):
			if index_check != current_index:
				return
		return True

	def resolve(self, kind, value, implicit, mark=None):
		if kind is nodes.ScalarNode and implicit[0]:
			if value == '':
				resolvers = self.yaml_implicit_resolvers.get('', [])
			else:
				resolvers = self.yaml_implicit_resolvers.get(value[0], [])
			resolvers += self.yaml_implicit_resolvers.get(None, [])
			for tag, regexp in resolvers:
				if regexp.match(value):
					return tag
			else:
				self.echoerr(
					'While resolving plain scalar', None,
					'expected floating-point value, integer, null or boolean, but got %r' % value,
					mark
				)
				return self.DEFAULT_SCALAR_TAG
		if kind is nodes.ScalarNode:
			return self.DEFAULT_SCALAR_TAG
		elif kind is nodes.SequenceNode:
			return self.DEFAULT_SEQUENCE_TAG
		elif kind is nodes.MappingNode:
			return self.DEFAULT_MAPPING_TAG


class Resolver(BaseResolver):
	pass


Resolver.add_implicit_resolver(
	'tag:yaml.org,2002:bool',
	re.compile(r'''^(?:true|false)$''', re.X),
	list('yYnNtTfFoO'))

Resolver.add_implicit_resolver(
	'tag:yaml.org,2002:float',
	re.compile(r'^-?(?:0|[1-9]\d*)(?=[.eE])(?:\.\d+)?(?:[eE][-+]?\d+)?$', re.X),
	list('-0123456789'))

Resolver.add_implicit_resolver(
	'tag:yaml.org,2002:int',
	re.compile(r'^(?:0|-?[1-9]\d*)$', re.X),
	list('-0123456789'))

Resolver.add_implicit_resolver(
	'tag:yaml.org,2002:null',
	re.compile(r'^null$', re.X),
	['n'])
