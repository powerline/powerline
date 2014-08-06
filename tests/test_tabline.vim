#!/usr/bin/vim -S
source powerline/bindings/vim/plugin/powerline.vim
edit abc
tabedit def
tabedit ghi

try
	let &columns = 80
	let result = eval(&tabline[2:])
catch
	call writefile(['Exception while evaluating &tabline', v:exception], 'message.fail')
	cquit
endtry

if result isnot# '%#Pl_240_5789784_235_2500134_NONE# 1 %#Pl_240_5789784_235_2500134_NONE#./%#Pl_244_8421504_235_2500134_bold#abc %#Pl_244_8421504_235_2500134_NONE# %#Pl_240_5789784_235_2500134_NONE#2 %#Pl_240_5789784_235_2500134_NONE#./%#Pl_244_8421504_235_2500134_bold#def %#Pl_235_2500134_240_5789784_NONE# %#Pl_250_12369084_240_5789784_NONE#./%#Pl_231_16777215_240_5789784_bold#ghi %#Pl_240_5789784_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                                           %#Pl_252_13684944_236_3158064_NONE# %#Pl_235_2500134_252_13684944_bold# Tabs '
	call writefile(['Unexpected tabline', result], 'message.fail')
	cquit
endif

tabonly!

try
	let result = eval(&tabline[2:])
catch
	call writefile(['Exception while evaluating &tabline', v:exception], 'message.fail')
	cquit
endtry

if result isnot# '%#Pl_240_5789784_235_2500134_NONE# ./%#Pl_244_8421504_235_2500134_bold#abc %#Pl_244_8421504_235_2500134_NONE# %#Pl_240_5789784_235_2500134_NONE#./%#Pl_244_8421504_235_2500134_bold#def %#Pl_235_2500134_240_5789784_NONE# %#Pl_250_12369084_240_5789784_NONE#./%#Pl_231_16777215_240_5789784_bold#ghi %#Pl_240_5789784_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                                               %#Pl_252_13684944_236_3158064_NONE# %#Pl_235_2500134_252_13684944_bold# Bufs '
	call writefile(['Unexpected tabline (2)', result], 'message.fail')
	cquit
endif

qall!
