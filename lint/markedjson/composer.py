# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lint.markedjson import nodes
from powerline.lint.markedjson import events
from powerline.lint.markedjson.error import MarkedError


__all__ = ['Composer', 'ComposerError']


class ComposerError(MarkedError):
	pass


class Composer:
	def __init__(self):
		pass

	def check_node(self):
		# Drop the STREAM-START event.
		if self.check_event(events.StreamStartEvent):
			self.get_event()

		# If there are more documents available?
		return not self.check_event(events.StreamEndEvent)

	def get_node(self):
		# Get the root node of the next document.
		if not self.check_event(events.StreamEndEvent):
			return self.compose_document()

	def get_single_node(self):
		# Drop the STREAM-START event.
		self.get_event()

		# Compose a document if the stream is not empty.
		document = None
		if not self.check_event(events.StreamEndEvent):
			document = self.compose_document()

		# Ensure that the stream contains no more documents.
		if not self.check_event(events.StreamEndEvent):
			event = self.get_event()
			raise ComposerError(
				'expected a single document in the stream',
				document.start_mark,
				'but found another document',
				event.start_mark
			)

		# Drop the STREAM-END event.
		self.get_event()

		return document

	def compose_document(self):
		# Drop the DOCUMENT-START event.
		self.get_event()

		# Compose the root node.
		node = self.compose_node(None, None)

		# Drop the DOCUMENT-END event.
		self.get_event()

		return node

	def compose_node(self, parent, index):
		self.descend_resolver(parent, index)
		if self.check_event(events.ScalarEvent):
			node = self.compose_scalar_node()
		elif self.check_event(events.SequenceStartEvent):
			node = self.compose_sequence_node()
		elif self.check_event(events.MappingStartEvent):
			node = self.compose_mapping_node()
		self.ascend_resolver()
		return node

	def compose_scalar_node(self):
		event = self.get_event()
		tag = event.tag
		if tag is None or tag == '!':
			tag = self.resolve(nodes.ScalarNode, event.value, event.implicit, event.start_mark)
		node = nodes.ScalarNode(tag, event.value, event.start_mark, event.end_mark, style=event.style)
		return node

	def compose_sequence_node(self):
		start_event = self.get_event()
		tag = start_event.tag
		if tag is None or tag == '!':
			tag = self.resolve(nodes.SequenceNode, None, start_event.implicit)
		node = nodes.SequenceNode(tag, [], start_event.start_mark, None, flow_style=start_event.flow_style)
		index = 0
		while not self.check_event(events.SequenceEndEvent):
			node.value.append(self.compose_node(node, index))
			index += 1
		end_event = self.get_event()
		node.end_mark = end_event.end_mark
		return node

	def compose_mapping_node(self):
		start_event = self.get_event()
		tag = start_event.tag
		if tag is None or tag == '!':
			tag = self.resolve(nodes.MappingNode, None, start_event.implicit)
		node = nodes.MappingNode(tag, [], start_event.start_mark, None, flow_style=start_event.flow_style)
		while not self.check_event(events.MappingEndEvent):
			# key_event = self.peek_event()
			item_key = self.compose_node(node, None)
			# if item_key in node.value:
			# 	 raise ComposerError('while composing a mapping', start_event.start_mark,
			# 			 'found duplicate key', key_event.start_mark)
			item_value = self.compose_node(node, item_key)
			# node.value[item_key] = item_value
			node.value.append((item_key, item_value))
		end_event = self.get_event()
		node.end_mark = end_event.end_mark
		return node
