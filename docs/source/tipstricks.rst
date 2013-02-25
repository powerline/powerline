*************
Tips & Tricks
*************

Vim
===

Fix terminal timeout when pressing escape
-----------------------------------------

When you're pressing :kbd:`Escape` to leave insert mode in the terminal, it 
will by default take a second or another keystroke to leave insert mode 
completely and update the statusline. If you find this annoying, you can add 
the following snippet to your :file:`vimrc` to escape insert mode 
immediately:

.. code-block:: vim

   if ! has('gui_running')
       augroup FastEscape
           autocmd!
           au InsertEnter * set ttimeoutlen=1
           au InsertLeave * set ttimeoutlen=-1
       augroup END
   endif

Useful settings
---------------

You may find the following vim settings useful when using the Powerline 
statusline:

.. code-block:: vim
   
   set laststatus=2 " Always display the statusline in all windows
   set noshowmode " Hide the default mode text (e.g. -- INSERT -- below the statusline)
