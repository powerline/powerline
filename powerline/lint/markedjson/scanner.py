# Scanner produces tokens of the following types:
# STREAM-START
# STREAM-END
# DOCUMENT-START
# DOCUMENT-END
# FLOW-SEQUENCE-START
# FLOW-MAPPING-START
# FLOW-SEQUENCE-END
# FLOW-MAPPING-END
# FLOW-ENTRY
# KEY
# VALUE
# SCALAR(value, plain, style)
#
# Read comments in the Scanner code for more details.

__all__ = ['Scanner', 'ScannerError']

from .error import MarkedError
from .tokens import *  # NOQA


class ScannerError(MarkedError):
	pass


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


class SimpleKey:
	# See below simple keys treatment.
	def __init__(self, token_number, index, line, column, mark):
		self.token_number = token_number
		self.index = index
		self.line = line
		self.column = column
		self.mark = mark


class Scanner:
	def __init__(self):
		"""Initialize the scanner."""
		# It is assumed that Scanner and Reader will have a common descendant.
		# Reader do the dirty work of checking for BOM and converting the
		# input data to Unicode. It also adds NUL to the end.
		#
		# Reader supports the following methods
		#	self.peek(i=0)		 # peek the next i-th character
		#	self.prefix(l=1)	 # peek the next l characters
		#	self.forward(l=1)	 # read the next l characters and move the pointer.

		# Had we reached the end of the stream?
		self.done = False

		# The number of unclosed '{' and '['. `flow_level == 0` means block
		# context.
		self.flow_level = 0

		# List of processed tokens that are not yet emitted.
		self.tokens = []

		# Add the STREAM-START token.
		self.fetch_stream_start()

		# Number of tokens that were emitted through the `get_token` method.
		self.tokens_taken = 0

		# Variables related to simple keys treatment.

		# A simple key is a key that is not denoted by the '?' indicator.
		# We emit the KEY token before all keys, so when we find a potential
		# simple key, we try to locate the corresponding ':' indicator.
		# Simple keys should be limited to a single line.

		# Can a simple key start at the current position? A simple key may
		# start:
		# - after '{', '[', ',' (in the flow context),
		self.allow_simple_key = False

		# Keep track of possible simple keys. This is a dictionary. The key
		# is `flow_level`; there can be no more that one possible simple key
		# for each level. The value is a SimpleKey record:
		#	(token_number, index, line, column, mark)
		# A simple key may start with SCALAR(flow), '[', or '{' tokens.
		self.possible_simple_keys = {}

	# Public methods.

	def check_token(self, *choices):
		# Check if the next token is one of the given types.
		while self.need_more_tokens():
			self.fetch_more_tokens()
		if self.tokens:
			if not choices:
				return True
			for choice in choices:
				if isinstance(self.tokens[0], choice):
					return True
		return False

	def peek_token(self):
		# Return the next token, but do not delete if from the queue.
		while self.need_more_tokens():
			self.fetch_more_tokens()
		if self.tokens:
			return self.tokens[0]

	def get_token(self):
		# Return the next token.
		while self.need_more_tokens():
			self.fetch_more_tokens()
		if self.tokens:
			self.tokens_taken += 1
			return self.tokens.pop(0)

	# Private methods.

	def need_more_tokens(self):
		if self.done:
			return False
		if not self.tokens:
			return True
		# The current token may be a potential simple key, so we
		# need to look further.
		self.stale_possible_simple_keys()
		if self.next_possible_simple_key() == self.tokens_taken:
			return True

	def fetch_more_tokens(self):

		# Eat whitespaces and comments until we reach the next token.
		self.scan_to_next_token()

		# Remove obsolete possible simple keys.
		self.stale_possible_simple_keys()

		# Peek the next character.
		ch = self.peek()

		# Is it the end of stream?
		if ch == '\0':
			return self.fetch_stream_end()

		# Note: the order of the following checks is NOT significant.

		# Is it the flow sequence start indicator?
		if ch == '[':
			return self.fetch_flow_sequence_start()

		# Is it the flow mapping start indicator?
		if ch == '{':
			return self.fetch_flow_mapping_start()

		# Is it the flow sequence end indicator?
		if ch == ']':
			return self.fetch_flow_sequence_end()

		# Is it the flow mapping end indicator?
		if ch == '}':
			return self.fetch_flow_mapping_end()

		# Is it the flow entry indicator?
		if ch == ',':
			return self.fetch_flow_entry()

		# Is it the value indicator?
		if ch == ':' and self.flow_level:
			return self.fetch_value()

		# Is it a double quoted scalar?
		if ch == '\"':
			return self.fetch_double()

		# It must be a plain scalar then.
		if self.check_plain():
			return self.fetch_plain()

		# No? It's an error. Let's produce a nice error message.
		raise ScannerError("while scanning for the next token", None,
				"found character %r that cannot start any token" % ch,
				self.get_mark())

	# Simple keys treatment.

	def next_possible_simple_key(self):
		# Return the number of the nearest possible simple key. Actually we
		# don't need to loop through the whole dictionary. We may replace it
		# with the following code:
		#	if not self.possible_simple_keys:
		#		return None
		#	return self.possible_simple_keys[
		#			min(self.possible_simple_keys.keys())].token_number
		min_token_number = None
		for level in self.possible_simple_keys:
			key = self.possible_simple_keys[level]
			if min_token_number is None or key.token_number < min_token_number:
				min_token_number = key.token_number
		return min_token_number

	def stale_possible_simple_keys(self):
		# Remove entries that are no longer possible simple keys. According to
		# the YAML specification, simple keys
		# - should be limited to a single line,
		# Disabling this procedure will allow simple keys of any length and
		# height (may cause problems if indentation is broken though).
		for level in list(self.possible_simple_keys):
			key = self.possible_simple_keys[level]
			if key.line != self.line:
				del self.possible_simple_keys[level]

	def save_possible_simple_key(self):
		# The next token may start a simple key. We check if it's possible
		# and save its position. This function is called for
		#	SCALAR(flow), '[', and '{'.

		# The next token might be a simple key. Let's save it's number and
		# position.
		if self.allow_simple_key:
			self.remove_possible_simple_key()
			token_number = self.tokens_taken + len(self.tokens)
			key = SimpleKey(token_number,
					self.index, self.line, self.column, self.get_mark())
			self.possible_simple_keys[self.flow_level] = key

	def remove_possible_simple_key(self):
		# Remove the saved possible key position at the current flow level.
		if self.flow_level in self.possible_simple_keys:
			del self.possible_simple_keys[self.flow_level]

	# Fetchers.

	def fetch_stream_start(self):
		# We always add STREAM-START as the first token and STREAM-END as the
		# last token.

		# Read the token.
		mark = self.get_mark()

		# Add STREAM-START.
		self.tokens.append(StreamStartToken(mark, mark,
			encoding=self.encoding))

	def fetch_stream_end(self):
		# Reset simple keys.
		self.remove_possible_simple_key()
		self.allow_simple_key = False
		self.possible_simple_keys = {}

		# Read the token.
		mark = self.get_mark()

		# Add STREAM-END.
		self.tokens.append(StreamEndToken(mark, mark))

		# The steam is finished.
		self.done = True

	def fetch_flow_sequence_start(self):
		self.fetch_flow_collection_start(FlowSequenceStartToken)

	def fetch_flow_mapping_start(self):
		self.fetch_flow_collection_start(FlowMappingStartToken)

	def fetch_flow_collection_start(self, TokenClass):

		# '[' and '{' may start a simple key.
		self.save_possible_simple_key()

		# Increase the flow level.
		self.flow_level += 1

		# Simple keys are allowed after '[' and '{'.
		self.allow_simple_key = True

		# Add FLOW-SEQUENCE-START or FLOW-MAPPING-START.
		start_mark = self.get_mark()
		self.forward()
		end_mark = self.get_mark()
		self.tokens.append(TokenClass(start_mark, end_mark))

	def fetch_flow_sequence_end(self):
		self.fetch_flow_collection_end(FlowSequenceEndToken)

	def fetch_flow_mapping_end(self):
		self.fetch_flow_collection_end(FlowMappingEndToken)

	def fetch_flow_collection_end(self, TokenClass):

		# Reset possible simple key on the current level.
		self.remove_possible_simple_key()

		# Decrease the flow level.
		self.flow_level -= 1

		# No simple keys after ']' or '}'.
		self.allow_simple_key = False

		# Add FLOW-SEQUENCE-END or FLOW-MAPPING-END.
		start_mark = self.get_mark()
		self.forward()
		end_mark = self.get_mark()
		self.tokens.append(TokenClass(start_mark, end_mark))

	def fetch_value(self):
		# Do we determine a simple key?
		if self.flow_level in self.possible_simple_keys:

			# Add KEY.
			key = self.possible_simple_keys[self.flow_level]
			del self.possible_simple_keys[self.flow_level]
			self.tokens.insert(key.token_number - self.tokens_taken,
					KeyToken(key.mark, key.mark))

			# There cannot be two simple keys one after another.
			self.allow_simple_key = False

		# Add VALUE.
		start_mark = self.get_mark()
		self.forward()
		end_mark = self.get_mark()
		self.tokens.append(ValueToken(start_mark, end_mark))

	def fetch_flow_entry(self):

		# Simple keys are allowed after ','.
		self.allow_simple_key = True

		# Reset possible simple key on the current level.
		self.remove_possible_simple_key()

		# Add FLOW-ENTRY.
		start_mark = self.get_mark()
		self.forward()
		end_mark = self.get_mark()
		self.tokens.append(FlowEntryToken(start_mark, end_mark))

	def fetch_double(self):
		# A flow scalar could be a simple key.
		self.save_possible_simple_key()

		# No simple keys after flow scalars.
		self.allow_simple_key = False

		# Scan and add SCALAR.
		self.tokens.append(self.scan_flow_scalar())

	def fetch_plain(self):

		self.save_possible_simple_key()

		# No simple keys after plain scalars.
		self.allow_simple_key = False

		# Scan and add SCALAR. May change `allow_simple_key`.
		self.tokens.append(self.scan_plain())

	# Checkers.

	def check_plain(self):
		return self.peek() in '0123456789-ntf'

	# Scanners.

	def scan_to_next_token(self):
		while self.peek() in ' \t\n':
			self.forward()

	def scan_flow_scalar(self):
		# See the specification for details.
		# Note that we loose indentation rules for quoted scalars. Quoted
		# scalars don't need to adhere indentation because " and ' clearly
		# mark the beginning and the end of them. Therefore we are less
		# restrictive then the specification requires. We only need to check
		# that document separators are not included in scalars.
		chunks = []
		start_mark = self.get_mark()
		quote = self.peek()
		self.forward()
		chunks.extend(self.scan_flow_scalar_non_spaces(start_mark))
		while self.peek() != quote:
			chunks.extend(self.scan_flow_scalar_spaces(start_mark))
			chunks.extend(self.scan_flow_scalar_non_spaces(start_mark))
		self.forward()
		end_mark = self.get_mark()
		return ScalarToken(unicode().join(chunks), False, start_mark, end_mark, '"')

	ESCAPE_REPLACEMENTS = {
		'b': '\x08',
		't': '\x09',
		'n': '\x0A',
		'f': '\x0C',
		'r': '\x0D',
		'\"': '\"',
		'\\': '\\',
	}

	ESCAPE_CODES = {
		'u': 4,
	}

	def scan_flow_scalar_non_spaces(self, start_mark):
		# See the specification for details.
		chunks = []
		while True:
			length = 0
			while self.peek(length) not in '\"\\\0 \t\n':
				length += 1
			if length:
				chunks.append(self.prefix(length))
				self.forward(length)
			ch = self.peek()
			if ch == '\\':
				self.forward()
				ch = self.peek()
				if ch in self.ESCAPE_REPLACEMENTS:
					chunks.append(self.ESCAPE_REPLACEMENTS[ch])
					self.forward()
				elif ch in self.ESCAPE_CODES:
					length = self.ESCAPE_CODES[ch]
					self.forward()
					for k in range(length):
						if self.peek(k) not in '0123456789ABCDEFabcdef':
							raise ScannerError("while scanning a double-quoted scalar", start_mark,
									"expected escape sequence of %d hexdecimal numbers, but found %r" %
										(length, self.peek(k)), self.get_mark())
					code = int(self.prefix(length), 16)
					chunks.append(chr(code))
					self.forward(length)
				else:
					raise ScannerError("while scanning a double-quoted scalar", start_mark,
							"found unknown escape character %r" % ch, self.get_mark())
			else:
				return chunks

	def scan_flow_scalar_spaces(self, start_mark):
		# See the specification for details.
		chunks = []
		length = 0
		while self.peek(length) in ' \t':
			length += 1
		whitespaces = self.prefix(length)
		self.forward(length)
		ch = self.peek()
		if ch == '\0':
			raise ScannerError("while scanning a quoted scalar", start_mark,
					"found unexpected end of stream", self.get_mark())
		elif ch == '\n':
			raise ScannerError("while scanning a quoted scalar", start_mark,
					"found unexpected line end", self.get_mark())
		else:
			chunks.append(whitespaces)
		return chunks

	def scan_plain(self):
		chunks = []
		start_mark = self.get_mark()
		spaces = []
		while True:
			length = 0
			while True:
				if self.peek(length) not in 'eE.0123456789nul-tr+fas':
					break
				length += 1
			if length == 0:
				break
			self.allow_simple_key = False
			chunks.extend(spaces)
			chunks.append(self.prefix(length))
			self.forward(length)
		end_mark = self.get_mark()
		return ScalarToken(''.join(chunks), True, start_mark, end_mark)
