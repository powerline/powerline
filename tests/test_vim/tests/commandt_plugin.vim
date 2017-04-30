#!/usr/bin/vim -S
set nocompatible
set columns=80
execute 'source' fnameescape(expand('<sfile>:p:h:h').'/vim_utils.vim')
call EnablePlugins('command-t')
call SourcePowerline()
let g:statusline_values = []
call PyFile('setup_statusline_catcher')
execute 'CommandTBuffer'|call feedkeys("\<C-c>")
call RunPython('powerline.render = _powerline_old_render')
let g:expected_statusline = '%#Pl_231_16777215_240_5789784_bold# Command-T %#Pl_231_16777215_240_5789784_NONE# %#Pl_231_16777215_240_5789784_bold#BufferFinder %#Pl_240_5789784_236_3158064_NONE# %#Pl_231_16777215_236_3158064_NONE#                                                    '
call CheckMessages()
if index(g:statusline_values, g:expected_statusline) == -1
	call CheckStatuslineValue(get(g:statusline_values, -1, ''), g:expected_statusline)
	cquit
endif
qall
