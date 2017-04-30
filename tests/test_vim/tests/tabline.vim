#!/usr/bin/vim -S
set encoding=utf-8
let g:powerline_config_paths = [expand('<sfile>:p:h:h:h:h') . '/powerline/config_files']
source <sfile>:p:h:h:h:h/powerline/bindings/vim/plugin/powerline.vim
edit abc
tabedit def
tabedit ghi

redir => g:messages

try
	let &columns = 80
	let result = eval(&tabline[2:])
catch
	call writefile(['Exception while evaluating &tabline', v:exception], 'message.fail')
	cquit
endtry

if result isnot# '%1T%#Pl_247_10395294_236_3158064_NONE# 1 ./abc %#Pl_244_8421504_236_3158064_NONE# %2T%#Pl_247_10395294_236_3158064_NONE#2 ./def %#Pl_236_3158064_240_5789784_NONE# %3T%#Pl_250_12369084_240_5789784_NONE#3 ./%#Pl_231_16777215_240_5789784_bold#ghi %#Pl_240_5789784_236_3158064_NONE# %T%#Pl_231_16777215_236_3158064_NONE#                                         %#Pl_252_13684944_236_3158064_NONE# %#Pl_235_2500134_252_13684944_bold# Tabs '
	call writefile(['Unexpected tabline', result], 'message.fail')
	cquit
endif

tabonly!

try
	let result = eval(&tabline[2:])
catch
	call writefile(['Exception while evaluating &tabline (2)', v:exception], 'message.fail')
	cquit
endtry

if result isnot# '%T%#Pl_247_10395294_236_3158064_NONE# 1 ./abc %#Pl_244_8421504_236_3158064_NONE# %#Pl_247_10395294_236_3158064_NONE#2 ./def %#Pl_236_3158064_240_5789784_NONE# %#Pl_250_12369084_240_5789784_NONE#3 ./%#Pl_231_16777215_240_5789784_bold#ghi %#Pl_240_5789784_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                                         %#Pl_252_13684944_236_3158064_NONE# %#Pl_235_2500134_252_13684944_bold# Bufs '
	call writefile(['Unexpected tabline (2)', result], 'message.fail')
	cquit
endif

try
	vsplit
	let result = eval(&tabline[2:])
catch
	call writefile(['Exception while evaluating &tabline (3)', v:exception], 'message.fail')
endtry

if result isnot# '%T%#Pl_247_10395294_236_3158064_NONE# 1 ./abc %#Pl_244_8421504_236_3158064_NONE# %#Pl_247_10395294_236_3158064_NONE#2 ./def %#Pl_236_3158064_240_5789784_NONE# %#Pl_250_12369084_240_5789784_NONE#3 ./%#Pl_231_16777215_240_5789784_bold#ghi %#Pl_240_5789784_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                                         %#Pl_252_13684944_236_3158064_NONE# %#Pl_235_2500134_252_13684944_bold# Bufs '
	call writefile(['Unexpected tabline (3)', result], 'message.fail')
	cquit
endif

redir END
if g:messages =~ '\S'
	call writefile(['Non-empty messages:', g:messages], 'message.fail')
	cquit
endif

qall!
