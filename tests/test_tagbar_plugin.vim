#!/usr/bin/vim -S
set nocompatible
set columns=80
execute 'source' fnameescape(expand('<sfile>:p:h').'/vim_utils.vim')
let g:powerline_theme_overrides__default={'segment_data':{'branch':{'display':0},'powerline.segments.vim.file_directory':{'display':0}}}
execute 'edit' fnameescape(g:root.'/tests/setup_statusline_catcher.py')
filetype plugin indent on
set filetype=python
call EnablePlugins('tagbar')
call SourcePowerline()
set laststatus=2
%change
'''Module'''
class SuperClass():
	'''Class'''
	def super_function():
		'''Function'''
		pass
.
redrawstatus
set columns=80
/Module
call CheckCurrentStatusline('%#Pl_22_24320_148_11523840_bold# NORMAL %#Pl_148_11523840_240_5789784_NONE# %#Pl_231_16777215_240_5789784_bold#setup_statusline_catcher.py%#Pl_220_16766720_240_5789784_bold# + %#Pl_240_5789784_236_3158064_NONE# %#Pl_250_12369084_236_3158064_NONE#%#Pl_231_16777215_236_3158064_NONE#  %#Pl_244_8421504_236_3158064_NONE# %#Pl_247_10395294_236_3158064_NONE# utf-8%#Pl_244_8421504_236_3158064_NONE# %#Pl_247_10395294_236_3158064_NONE# python%#Pl_240_5789784_236_3158064_NONE# %#Pl_70_6598190_240_5789784_NONE#  17%%%#Pl_252_13684944_240_5789784_NONE# %#Pl_235_2500134_252_13684944_NONE#  %#Pl_235_2500134_252_13684944_bold#  1%#Pl_22_24576_252_13684944_NONE#:1  ')
/Class
call CheckCurrentStatusline('%#Pl_22_24320_148_11523840_bold# NORMAL %#Pl_148_11523840_240_5789784_NONE# %#Pl_231_16777215_240_5789784_bold#setup_statusline_catcher.py%#Pl_220_16766720_240_5789784_bold# + %#Pl_240_5789784_236_3158064_NONE# %#Pl_250_12369084_236_3158064_NONE#SuperClass%#Pl_231_16777215_236_3158064_NONE#%#Pl_244_8421504_236_3158064_NONE# %#Pl_247_10395294_236_3158064_NONE# python%#Pl_240_5789784_236_3158064_NONE# %#Pl_107_7514952_240_5789784_NONE#  33%%%#Pl_252_13684944_240_5789784_NONE# %#Pl_235_2500134_252_13684944_NONE#  %#Pl_235_2500134_252_13684944_bold#  2%#Pl_22_24576_252_13684944_NONE#:1  ')
qall!
