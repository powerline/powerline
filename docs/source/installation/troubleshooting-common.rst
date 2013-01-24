I'm using tmux and Powerline looks like crap, what's wrong?
-----------------------------------------------------------

* You need to tell tmux that it has 256-color capabilities. Add this to your 
  :file:`.tmux.conf` to solve this issue::

    set -g default-terminal "screen-256color"

* If you're using iTerm2, make sure that you have enabled the setting 
  :guilabel:`Set locale variables automatically` in :menuselection:`Profiles 
  --> Terminal --> Environment`.

My vim statusline has strange characters like ``^B`` in it!
-----------------------------------------------------------

* Please add ``set encoding=utf-8`` to your :file:`vimrc`.

My vim statusline has a lot of ``^`` or underline characters in it!
-------------------------------------------------------------------

* You need to configure the ``fillchars`` setting to disable statusline 
  fillchars (see ``:h fillchars`` for details). Add this to your 
  :file:`vimrc` to solve this issue:

   .. code-block:: vim

      set fillchars+=stl:\ ,stlnc:\ 

My vim statusline is hidden/only appears in split windows!
----------------------------------------------------------

* Make sure that you have ``set laststatus=2`` in your :file:`vimrc`.
