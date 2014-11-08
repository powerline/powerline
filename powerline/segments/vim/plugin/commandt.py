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
				@active_finder.class.name
			end
		end
		if (not ($command_t.respond_to? 'path'))
			def $command_t.path
				@path
			end
		end
		def $powerline.commandt_set_active_finder
			::VIM::command "let g:powerline_commandt_reply = '#{$command_t.active_finder}'"
		end
		def $powerline.commandt_set_path
			::VIM::command "let g:powerline_commandt_reply = '#{$command_t.path.gsub(/'/, "''")}'"
		end
		'''
	))


initialized = False


def finder(pl):
	'''Display Command-T finder name

	Requires $command_t.active_finder and .path methods (code above may 
	monkey-patch $command_t to add them).
	'''
	initialize()
	vim.command('ruby $powerline.commandt_set_active_finder')
	return [{
		'highlight_group': ['commandt:finder'],
		'contents': vim.eval('g:powerline_commandt_reply').replace('CommandT::', '')
	}]


FINDERS_WITHOUT_PATH = set((
	'CommandT::MRUBufferFinder',
	'CommandT::BufferFinder',
	'CommandT::TagFinder',
	'CommandT::JumpFinder',
))


def path(pl):
	initialize()
	vim.command('ruby $powerline.commandt_set_active_finder')
	finder = vim.eval('g:powerline_commandt_reply')
	if finder in FINDERS_WITHOUT_PATH:
		return None
	vim.command('ruby $powerline.commandt_set_path')
	return [{
		'highlight_group': ['commandt:path'],
		'contents': vim.eval('g:powerline_commandt_reply')
	}]
