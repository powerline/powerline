# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.lint.markedjson.error import MarkedError
from powerline.lint.markedjson import tokens
from powerline.lint.markedjson import events


class ParserError(MarkedError):
	pass


class Parser:
	def __init__(self):
		self.current_event = None
		self.yaml_version = None
		self.states = []
		self.marks = []
		self.state = self.parse_stream_start

	def dispose(self):
		# Reset the state attributes (to clear self-references)
		self.states = []
		self.state = None

	def check_event(self, *choices):
		# Check the type of the next event.
		if self.current_event is None:
			if self.state:
				self.current_event = self.state()
		if self.current_event is not None:
			if not choices:
				return True
			for choice in choices:
				if isinstance(self.current_event, choice):
					return True
		return False

	def peek_event(self):
		# Get the next event.
		if self.current_event is None:
			if self.state:
				self.current_event = self.state()
		return self.current_event

	def get_event(self):
		# Get the next event and proceed further.
		if self.current_event is None:
			if self.state:
				self.current_event = self.state()
		value = self.current_event
		self.current_event = None
		return value

	# stream	::= STREAM-START implicit_document? explicit_document* STREAM-END
	# implicit_document ::= block_node DOCUMENT-END*
	# explicit_document ::= DIRECTIVE* DOCUMENT-START block_node? DOCUMENT-END*

	def parse_stream_start(self):
		# Parse the stream start.
		token = self.get_token()
		event = events.StreamStartEvent(token.start_mark, token.end_mark, encoding=token.encoding)

		# Prepare the next state.
		self.state = self.parse_implicit_document_start

		return event

	def parse_implicit_document_start(self):
		# Parse an implicit document.
		if not self.check_token(tokens.StreamEndToken):
			token = self.peek_token()
			start_mark = end_mark = token.start_mark
			event = events.DocumentStartEvent(start_mark, end_mark, explicit=False)

			# Prepare the next state.
			self.states.append(self.parse_document_end)
			self.state = self.parse_node

			return event

		else:
			return self.parse_document_start()

	def parse_document_start(self):
		# Parse an explicit document.
		if not self.check_token(tokens.StreamEndToken):
			token = self.peek_token()
			self.echoerr(
				None, None,
				('expected \'<stream end>\', but found %r' % token.id), token.start_mark
			)
			return events.StreamEndEvent(token.start_mark, token.end_mark)
		else:
			# Parse the end of the stream.
			token = self.get_token()
			event = events.StreamEndEvent(token.start_mark, token.end_mark)
			assert not self.states
			assert not self.marks
			self.state = None
		return event

	def parse_document_end(self):
		# Parse the document end.
		token = self.peek_token()
		start_mark = end_mark = token.start_mark
		explicit = False
		event = events.DocumentEndEvent(start_mark, end_mark, explicit=explicit)

		# Prepare the next state.
		self.state = self.parse_document_start

		return event

	def parse_document_content(self):
		return self.parse_node()

	def parse_node(self, indentless_sequence=False):
		start_mark = end_mark = None
		if start_mark is None:
			start_mark = end_mark = self.peek_token().start_mark
		event = None
		implicit = True
		if self.check_token(tokens.ScalarToken):
			token = self.get_token()
			end_mark = token.end_mark
			if token.plain:
				implicit = (True, False)
			else:
				implicit = (False, True)
			event = events.ScalarEvent(implicit, token.value, start_mark, end_mark, style=token.style)
			self.state = self.states.pop()
		elif self.check_token(tokens.FlowSequenceStartToken):
			end_mark = self.peek_token().end_mark
			event = events.SequenceStartEvent(implicit, start_mark, end_mark, flow_style=True)
			self.state = self.parse_flow_sequence_first_entry
		elif self.check_token(tokens.FlowMappingStartToken):
			end_mark = self.peek_token().end_mark
			event = events.MappingStartEvent(implicit, start_mark, end_mark, flow_style=True)
			self.state = self.parse_flow_mapping_first_key
		else:
			token = self.peek_token()
			raise ParserError(
				'while parsing a flow node', start_mark,
				'expected the node content, but found %r' % token.id,
				token.start_mark
			)
		return event

	def parse_flow_sequence_first_entry(self):
		token = self.get_token()
		self.marks.append(token.start_mark)
		return self.parse_flow_sequence_entry(first=True)

	def parse_flow_sequence_entry(self, first=False):
		if not self.check_token(tokens.FlowSequenceEndToken):
			if not first:
				if self.check_token(tokens.FlowEntryToken):
					self.get_token()
					if self.check_token(tokens.FlowSequenceEndToken):
						token = self.peek_token()
						self.echoerr(
							'While parsing a flow sequence', self.marks[-1],
							('expected sequence value, but got %r' % token.id), token.start_mark
						)
				else:
					token = self.peek_token()
					raise ParserError(
						'while parsing a flow sequence', self.marks[-1],
						('expected \',\' or \']\', but got %r' % token.id), token.start_mark
					)

			if not self.check_token(tokens.FlowSequenceEndToken):
				self.states.append(self.parse_flow_sequence_entry)
				return self.parse_node()
		token = self.get_token()
		event = events.SequenceEndEvent(token.start_mark, token.end_mark)
		self.state = self.states.pop()
		self.marks.pop()
		return event

	def parse_flow_sequence_entry_mapping_end(self):
		self.state = self.parse_flow_sequence_entry
		token = self.peek_token()
		return events.MappingEndEvent(token.start_mark, token.start_mark)

	def parse_flow_mapping_first_key(self):
		token = self.get_token()
		self.marks.append(token.start_mark)
		return self.parse_flow_mapping_key(first=True)

	def parse_flow_mapping_key(self, first=False):
		if not self.check_token(tokens.FlowMappingEndToken):
			if not first:
				if self.check_token(tokens.FlowEntryToken):
					self.get_token()
					if self.check_token(tokens.FlowMappingEndToken):
						token = self.peek_token()
						self.echoerr(
							'While parsing a flow mapping', self.marks[-1],
							('expected mapping key, but got %r' % token.id), token.start_mark
						)
				else:
					token = self.peek_token()
					raise ParserError(
						'while parsing a flow mapping', self.marks[-1],
						('expected \',\' or \'}\', but got %r' % token.id), token.start_mark
					)
			if self.check_token(tokens.KeyToken):
				token = self.get_token()
				if not self.check_token(tokens.ValueToken, tokens.FlowEntryToken, tokens.FlowMappingEndToken):
					self.states.append(self.parse_flow_mapping_value)
					return self.parse_node()
				else:
					token = self.peek_token()
					raise ParserError(
						'while parsing a flow mapping', self.marks[-1],
						('expected value, but got %r' % token.id), token.start_mark
					)
			elif not self.check_token(tokens.FlowMappingEndToken):
				token = self.peek_token()
				expect_key = self.check_token(tokens.ValueToken, tokens.FlowEntryToken)
				if not expect_key:
					self.get_token()
					expect_key = self.check_token(tokens.ValueToken)

				if expect_key:
					raise ParserError(
						'while parsing a flow mapping', self.marks[-1],
						('expected string key, but got %r' % token.id), token.start_mark
					)
				else:
					token = self.peek_token()
					raise ParserError(
						'while parsing a flow mapping', self.marks[-1],
						('expected \':\', but got %r' % token.id), token.start_mark
					)
		token = self.get_token()
		event = events.MappingEndEvent(token.start_mark, token.end_mark)
		self.state = self.states.pop()
		self.marks.pop()
		return event

	def parse_flow_mapping_value(self):
		if self.check_token(tokens.ValueToken):
			token = self.get_token()
			if not self.check_token(tokens.FlowEntryToken, tokens.FlowMappingEndToken):
				self.states.append(self.parse_flow_mapping_key)
				return self.parse_node()

		token = self.peek_token()
		raise ParserError(
			'while parsing a flow mapping', self.marks[-1],
			('expected mapping value, but got %r' % token.id), token.start_mark
		)
