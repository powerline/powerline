#!/usr/bin/vim -S
set nocompatible
set columns=80
execute 'source' fnameescape(expand('<sfile>:p:h').'/vim_utils.vim')
call EnablePlugins('nerdtree')
call SourcePowerline()
NERDTree /home
redrawstatus
call CheckCurrentStatusline('%#Pl_231_16777215_240_5789784_bold# /home %#Pl_240_5789784_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                      ')
call CheckMessages()
qall
