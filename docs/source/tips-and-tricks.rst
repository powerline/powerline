***************
Tips and tricks
***************

Vim
===

Useful settings
---------------

You may find the following vim settings useful when using the Powerline
statusline:

.. code-block:: vim

   set laststatus=2 " Always display the statusline in all windows
   set noshowmode " Hide the default mode text (e.g. -- INSERT -- below the statusline)

Terminus font and urxvt
=======================

The Terminus fonts does not have the powerline glyths and unless someone submits a patch to 
the font author, it is unlikely to happen.  However, Andre Klärner came up with this work around: 
In your ``~/.Xdefault`` file add the following:

``urxvt*font: xft:Terminus:pixelsize=12,xft:Inconsolata\ for\ Powerline:pixelsize=12``

This will allow urxvt to fallback onto the Inconsolata fonts in case it does not find the right 
glyths within the terminus font.
