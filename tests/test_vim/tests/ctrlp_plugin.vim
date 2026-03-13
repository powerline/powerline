#!/usr/bin/vim -S
set nocompatible
set columns=80
execute 'source' fnameescape(expand('<sfile>:p:h:h').'/vim_utils.vim')
call EnablePlugins('ctrlp.vim')
call SourcePowerline()
let g:statusline_values = []
call PyFile('setup_statusline_catcher')
execute 'CtrlPBuffer'
call RunPython('powerline.render = _powerline_old_render')
let g:expected_statusline = '%#Pl_231_16777215_240_5789784_bold# ControlP %#Pl_231_16777215_240_5789784_NONE# %#Pl_231_16777215_240_5789784_bold#fil %#Pl_231_16777215_236_3158064_NONE# buffers %#Pl_231_16777215_240_5789784_bold# mru %#Pl_231_16777215_236_3158064_NONE#                                                  '
call CheckMessages()
if index(g:statusline_values, g:expected_statusline) == -1
	call CheckStatuslineValue(get(g:statusline_values, -1, ''), g:expected_statusline)
	cquit
endif
qall
