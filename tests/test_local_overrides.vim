#!/usr/bin/vim -S
set encoding=utf-8
let g:powerline_config_paths = [expand('<sfile>:p:h:h') . '/powerline/config_files']
let g:powerline_config_overrides = {'common': {'default_top_theme': 'ascii'}}
let g:powerline_theme_overrides = {'default': {'segment_data': {'line_current_symbol': {'contents': 'LN '}, 'branch': {'before': 'B '}}}}

redir => g:messages

try
	python import powerline.vim
	let pycmd = 'python'
catch
	try
		python3 import powerline.vim
		let pycmd = 'python3'
	catch
		call writefile(['Unable to determine python version', v:exception], 'message.fail')
		cquit
	endtry
endtry

try
	execute pycmd 'powerline.vim.setup()'
catch
	call writefile(['Failed to run setup function', v:exception], 'message.fail')
	cquit
endtry

try
	let &columns = 80
	let result = eval(&statusline[2:])
catch
	call writefile(['Exception while evaluating &stl', v:exception], 'message.fail')
	cquit
endtry

if result isnot# '%#Pl_22_24320_148_11523840_bold# NORMAL %#Pl_148_11523840_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                                                 %#Pl_247_10395294_236_3158064_NONE#unix%#Pl_240_5789784_236_3158064_NONE# %#Pl_247_10329757_240_5789784_NONE# 100%%%#Pl_252_13684944_240_5789784_NONE# %#Pl_235_2500134_252_13684944_NONE# LN %#Pl_235_2500134_252_13684944_bold#  1%#Pl_22_24576_252_13684944_NONE#:1  '
	call writefile(['Unexpected result', result], 'message.fail')
	cquit
endif

redir END
if g:messages =~ '\S'
	call writefile(['Non-empty messages:', g:messages], 'message.fail')
	cquit
endif

qall!
