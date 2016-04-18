# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re
import codecs

from collections import namedtuple
from argparse import REMAINDER

from functools import reduce

from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import unchanged_required
from docutils import nodes

from powerline.lib.unicode import u


AUTHOR_LINE_START = '* `'
GLYPHS_AUTHOR_LINE_START = '* The glyphs in the font patcher are created by '


def get_authors():
	credits_file = os.path.join(os.path.dirname(__file__), 'license-and-credits.rst')
	authors = []
	glyphs_author = None
	with codecs.open(credits_file, encoding='utf-8') as CF:
		section = None
		prev_line = None
		for line in CF:
			line = line[:-1]
			if line and not line.replace('-', ''):
				section = prev_line
			elif section == 'Authors':
				if line.startswith(AUTHOR_LINE_START):
					authors.append(line[len(AUTHOR_LINE_START):line.index('<')].strip())
			elif section == 'Contributors':
				if line.startswith(GLYPHS_AUTHOR_LINE_START):
					assert(not glyphs_author)
					glyphs_author = line[len(GLYPHS_AUTHOR_LINE_START):line.index(',')].strip()
			prev_line = line
	return {
		'authors': ', '.join(authors),
		'glyphs_author': glyphs_author,
	}


class AutoManSubparsers(object):
	def __init__(self):
		self.parsers = []

	def add_parser(self, command, *args, **kwargs):
		self.parsers.append((command, AutoManParser(*args, **kwargs)))
		return self.parsers[-1][1]


Argument = namedtuple('Argument', ('names', 'help', 'choices', 'metavar', 'required', 'nargs', 'is_option', 'is_long_option', 'is_short_option', 'multi', 'can_be_joined'))


def parse_argument(*args, **kwargs):
	is_option = args[0].startswith('-')
	is_long_option = args[0].startswith('--')
	is_short_option = is_option and not is_long_option
	action = kwargs.get('action', 'store')
	multi = kwargs.get('action') in ('append',) or kwargs.get('nargs') is REMAINDER
	nargs = kwargs.get('nargs', (1 if action in ('append', 'store') else 0))
	return Argument(
		names=args,
		help=u(kwargs.get('help', '')),
		choices=[str(choice) for choice in kwargs.get('choices', [])],
		metavar=kwargs.get('metavar') or args[-1].lstrip('-').replace('-', '_').upper(),
		required=kwargs.get('required', False) if is_option else (
			kwargs.get('nargs') not in ('?',)),
		nargs=nargs,
		multi=multi,
		is_option=is_option,
		is_long_option=is_long_option,
		is_short_option=is_short_option,
		can_be_joined=(is_short_option and not multi and not nargs)
	)


class AutoManGroup(object):
	is_short_option = False
	is_option = False
	is_long_option = False
	can_be_joined = False

	def __init__(self):
		self.arguments = []
		self.required = False

	def add_argument(self, *args, **kwargs):
		self.arguments.append(parse_argument(*args, **kwargs))

	def add_argument_group(self, *args, **kwargs):
		self.arguments.append(AutoManGroup())
		return self.arguments[-1]


class SurroundWith():
	def __init__(self, ret, condition, start='[', end=']'):
		self.ret = ret
		self.condition = condition
		self.start = start
		self.end = end

	def __enter__(self, *args):
		if self.condition:
			self.ret.append(nodes.Text(self.start))

	def __exit__(self, *args):
		if self.condition:
			self.ret.append(nodes.Text(self.end))


def insert_separators(ret, sep):
	for i in range(len(ret) - 1, 0, -1):
		ret.insert(i, nodes.Text(sep))
	return ret


def format_usage_arguments(arguments, base_length=None):
	line = []
	prev_argument = None
	arg_indexes = [0]
	arguments = arguments[:]
	while arguments:
		argument = arguments.pop(0)
		if isinstance(argument, nodes.Text):
			line += [argument]
			continue
		can_join_arguments = (
			argument.is_short_option
			and prev_argument
			and prev_argument.can_be_joined
			and prev_argument.required == argument.required
		)
		if (
			prev_argument
			and not prev_argument.required
			and prev_argument.can_be_joined
			and not can_join_arguments
		):
			line.append(nodes.Text(']'))
		arg_indexes.append(len(line))
		if isinstance(argument, AutoManGroup):
			arguments = (
				[nodes.Text(' (')]
				+ insert_separators(argument.arguments[:], nodes.Text(' |'))
				+ [nodes.Text(' )')]
				+ arguments
			)
		else:
			if not can_join_arguments:
				line.append(nodes.Text(' '))
			with SurroundWith(line, not argument.required and not argument.can_be_joined):
				if argument.can_be_joined and not can_join_arguments and not argument.required:
					line.append(nodes.Text('['))
				if argument.is_option:
					line.append(nodes.strong())
					name = argument.names[0]
					if can_join_arguments:
						name = name[1:]
					# `--` is automatically transformed into &#8211; (EN DASH) 
					# when parsing into HTML. We do not need this.
					line[-1] += [nodes.Text(char) for char in name]
				elif argument.nargs is REMAINDER:
					line.append(nodes.Text('['))
					line.append(nodes.strong())
					line[-1] += [nodes.Text(char) for char in '--']
					line.append(nodes.Text('] '))
				if argument.nargs:
					assert(argument.nargs in (1, '?', REMAINDER))
					with SurroundWith(
						line, (
							True
							if argument.nargs is REMAINDER
							else (argument.nargs == '?' and argument.is_option)
						)
					):
						if argument.is_long_option:
							line.append(nodes.Text('='))
						line.append(nodes.emphasis(text=argument.metavar))
				elif not argument.is_option:
					line.append(nodes.strong(text=argument.metavar))
			if argument.multi:
				line.append(nodes.Text('…'))
		prev_argument = argument
	if (
		prev_argument
		and prev_argument.can_be_joined
		and not prev_argument.required
	):
		line.append(nodes.Text(']'))
	arg_indexes.append(len(line))
	ret = []
	if base_length is None:
		ret = line
	else:
		length = base_length
		prev_arg_idx = arg_indexes.pop(0)
		while arg_indexes:
			next_arg_idx = arg_indexes.pop(0)
			arg_length = sum((len(element.astext()) for element in line[prev_arg_idx:next_arg_idx]))
			if length + arg_length > 68:
				ret.append(nodes.Text('\n' + (' ' * base_length)))
				length = base_length
			ret += line[prev_arg_idx:next_arg_idx]
			length += arg_length
			prev_arg_idx = next_arg_idx
	return ret


LITERAL_RE = re.compile(r"`(.*?)'")


def parse_argparse_text(text):
	rst_text = LITERAL_RE.subn(r'``\1``', text)[0]
	ret = []
	for i, text in enumerate(rst_text.split('``')):
		if i % 2 == 0:
			ret.append(nodes.Text(text))
		else:
			ret.append(nodes.literal(text=text))
	return ret


def flatten_groups(arguments):
	for argument in arguments:
		if isinstance(argument, AutoManGroup):
			for group_argument in flatten_groups(argument.arguments):
				yield group_argument
		else:
			yield argument


def format_arguments(arguments):
	return [nodes.definition_list(
		'', *[
			nodes.definition_list_item(
				'',
				nodes.term(
					# node.Text('') is required because otherwise for some 
					# reason first name node is seen in HTML output as 
					# `<strong>abc</strong>`.
					'', *([nodes.Text('')] + (
						insert_separators([
							nodes.strong('', '', *[nodes.Text(ch) for ch in name])
							for name in argument.names
						], ', ')
						if argument.is_option else
						# Unless node.Text('') is here metavar is written in 
						# bold in the man page.
						[nodes.Text(''), nodes.emphasis(text=argument.metavar)]
					) + (
						[] if not argument.is_option or not argument.nargs else
						[nodes.Text(' '), nodes.emphasis('', argument.metavar)]
					))
				),
				nodes.definition('', nodes.paragraph('', *parse_argparse_text(argument.help or ''))),
			)
			for argument in flatten_groups(arguments)
		] + [
			nodes.definition_list_item(
				'',
				nodes.term(
					'', nodes.Text(''),
					nodes.strong(text='-h'),
					nodes.Text(', '),
					nodes.strong('', '', nodes.Text('-'), nodes.Text('-help')),
				),
				nodes.definition('', nodes.paragraph('', nodes.Text('Display help and exit.')))
			)
		]
	)]


def format_subcommand_usage(arguments, subcommands, progname, base_length):
	return reduce((lambda a, b: a + reduce((lambda c, d: c + d), b, [])), [
		[
			[progname]
			+ format_usage_arguments(arguments)
			+ [nodes.Text(' '), nodes.strong(text=subcmd)]
			+ format_usage_arguments(subparser.arguments)
			+ [nodes.Text('\n')]
			for subcmd, subparser in subparsers.parsers
		]
		for subparsers in subcommands
	], [])


def format_subcommands(subcommands):
	return reduce((lambda a, b: a + reduce((lambda c, d: c + d), b, [])), [
		[
			[
				nodes.section(
					'',
					nodes.title(text='Arguments specific to ' + subcmd + ' subcommand'),
					*format_arguments(subparser.arguments),
					ids=['subcmd-' + subcmd]
				)
			]
			for subcmd, subparser in subparsers.parsers
		]
		for subparsers in subcommands
	], [])


class AutoManParser(object):
	def __init__(self, description=None, help=None):
		self.description = description
		self.help = help
		self.arguments = []
		self.subcommands = []

	def add_argument(self, *args, **kwargs):
		self.arguments.append(parse_argument(*args, **kwargs))

	def add_subparsers(self):
		self.subcommands.append(AutoManSubparsers())
		return self.subcommands[-1]

	def add_mutually_exclusive_group(self):
		self.arguments.append(AutoManGroup())
		return self.arguments[-1]

	def automan_usage(self, prog):
		block = nodes.literal_block()
		progname = nodes.strong()
		progname += [nodes.Text(prog)]
		base_length = len(prog)
		if self.subcommands:
			block += format_subcommand_usage(self.arguments, self.subcommands, progname, base_length)
		else:
			block += [progname]
			block += format_usage_arguments(self.arguments, base_length)
		return [block]

	def automan_description(self):
		ret = []
		if self.help:
			ret += parse_argparse_text(self.help)
		ret += format_arguments(self.arguments) + format_subcommands(self.subcommands)
		return ret


class AutoMan(Directive):
	required_arguments = 1
	optional_arguments = 0
	option_spec = dict(prog=unchanged_required, minimal=bool)
	has_content = False

	def run(self):
		minimal = self.options.get('minimal')
		module = self.arguments[0]
		template_args = {}
		template_args.update(get_authors())
		get_argparser = __import__(str(module), fromlist=[str('get_argparser')]).get_argparser
		parser = get_argparser(AutoManParser)
		if minimal:
			container = nodes.container()
			container += parser.automan_usage(self.options['prog'])
			container += parser.automan_description()
			return [container]
		synopsis_section = nodes.section(
			'',
			nodes.title(text='Synopsis'),
			ids=['synopsis-section'],
		)
		synopsis_section += parser.automan_usage(self.options['prog'])
		description_section = nodes.section(
			'', nodes.title(text='Description'),
			ids=['description-section'],
		)
		description_section += parser.automan_description()
		author_section = nodes.section(
			'', nodes.title(text='Author'),
			nodes.paragraph(
				'',
				nodes.Text('Written by {authors} and contributors. The glyphs in the font patcher are created by {glyphs_author}.'.format(
					**get_authors()
				))
			),
			ids=['author-section']
		)
		issues_url = 'https://github.com/powerline/powerline/issues'
		reporting_bugs_section = nodes.section(
			'', nodes.title(text='Reporting bugs'),
			nodes.paragraph(
				'',
				nodes.Text('Report {prog} bugs to '.format(
					prog=self.options['prog'])),
				nodes.reference(
					issues_url, issues_url,
					refuri=issues_url,
					internal=False,
				),
				nodes.Text('.'),
			),
			ids=['reporting-bugs-section']
		)
		return [synopsis_section, description_section, author_section, reporting_bugs_section]


def setup(app):
	app.add_directive('automan', AutoMan)
