# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
    import vim
except ImportError:
    vim = object()

import os

from powerline.bindings.vim import buffer_name

initialized = False
def ctrlp(matcher_info):
    name = buffer_name(matcher_info)
    result = name and os.path.basename(name) == b'ControlP'
    global initialized
    if initialized:
        return result
    initialized = True
    vim.command('let g:_powerline_ctrlp_status = {}')
    vim.command(
        '''
        function! Ctrlp_status_main(focus, byfname, regex, prev, item, next, marked)
        let g:_powerline_ctrlp_status = {\
        "focus": a:focus,\
        "byfname": a:byfname,\
        "regex": a:regex,\
        "prev": a:prev,\
        "item": a:item,\
        "next": a:next,\
        "marked": a:marked,\
    }
        return ""
        endfunction
        '''
    )
    vim.command(
        '''
        function! Ctrlp_status_prog(str)
        let g:_powerline_ctrlp_status["prog"] = a:str
        return ""
        endfunction
        '''
    )
    vim.command(
        '''
        let g:ctrlp_status_func = {\
        'main': 'Ctrlp_status_main',\
        'prog': 'Ctrlp_status_prog',\
    }
        '''
    )
    return result
