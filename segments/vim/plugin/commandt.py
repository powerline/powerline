# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
	import vim
except ImportError:
	vim = object()

from powerline.bindings.vim import create_ruby_dpowerline


def initialize():
	global initialized
	if initialized:
		return
	initialized = True
	create_ruby_dpowerline()
	vim.command((
		# When using :execute (vim.command uses the same code) one should not 
		# use << EOF.
		'''
		ruby
		if (not ($command_t.respond_to? 'active_finder'))
			def $command_t.active_finder
				@active_finder and @active_finder.class.name or ''
			end
		end
		if (not ($command_t.respond_to? 'path'))
			def $command_t.path
				@path or ''
			end
		end
		def $powerline.commandt_set_active_finder
			::VIM::command "let g:powerline_commandt_reply = '#{$command_t.active_finder}'"
		end
		def $powerline.commandt_set_path
			::VIM::command "let g:powerline_commandt_reply = '#{($command_t.path or '').gsub(/'/, "''")}'"
		end
		'''
	))


initialized = False


def finder(pl):
	'''Display Command-T finder name

	Requires $command_t.active_finder and methods (code above may monkey-patch 
	$command_t to add them). All Command-T finders have ``CommandT::`` module 
	prefix, but it is stripped out (actually, any ``CommandT::`` substring will 
	be stripped out).

	Highlight groups used: ``commandt:finder``.
	'''
	initialize()
	vim.command('ruby $powerline.commandt_set_active_finder')
	return [{
		'highlight_groups': ['commandt:finder'],
		'contents': vim.eval('g:powerline_commandt_reply').replace('CommandT::', '').replace('Finder::', '')
	}]


FINDERS_WITHOUT_PATH = set((
	'CommandT::MRUBufferFinder',
	'CommandT::BufferFinder',
	'CommandT::TagFinder',
	'CommandT::JumpFinder',
	'CommandT::Finder::MRUBufferFinder',
	'CommandT::Finder::BufferFinder',
	'CommandT::Finder::TagFinder',
	'CommandT::Finder::JumpFinder',
))


def path(pl):
	'''Display path used by Command-T

	Requires $command_t.active_finder and .path methods (code above may 
	monkey-patch $command_t to add them).

	$command_t.active_finder is required in order to omit displaying path for 
	finders ``MRUBufferFinder``, ``BufferFinder``, ``TagFinder`` and 
	``JumpFinder`` (pretty much any finder, except ``FileFinder``).

	Highlight groups used: ``commandt:path``.
	'''
	initialize()
	vim.command('ruby $powerline.commandt_set_active_finder')
	finder = vim.eval('g:powerline_commandt_reply')
	if finder in FINDERS_WITHOUT_PATH:
		return None
	vim.command('ruby $powerline.commandt_set_path')
	return [{
		'highlight_groups': ['commandt:path'],
		'contents': vim.eval('g:powerline_commandt_reply')
	}]
