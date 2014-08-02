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

Rxvt-unicode
============

Terminus font and urxvt
-----------------------

The Terminus fonts does not have the powerline glyphs and unless someone submits 
a patch to the font author, it is unlikely to happen.  However, Andre Klärner 
came up with this work around: In your ``~/.Xdefault`` file add the following::

  urxvt*font: xft:Terminus:pixelsize=12,xft:Inconsolata\ for\ Powerline:pixelsize=12

This will allow urxvt to fallback onto the Inconsolata fonts in case it does not 
find the right glyphs within the terminus font.

Source Code Pro font and urxvt
------------------------------

Much like the terminus font that was mentioned above, a similar fix can be 
applied to the Source Code Pro fonts.

In the ``~/.Xdefaults`` add the following::

    URxvt*font: xft:Source\ Code\ Pro\ Medium:pixelsize=13:antialias=true:hinting=true,xft:Source\ Code\ Pro\ Medium:pixelsize=13:antialias=true:hinting=true

I noticed that Source Code Pro has the glyphs there already, but the pixel size 
of the fonts play a role in whether or not the > or the < separators showing up 
or not. Using font size 12, glyphs on the right hand side of the powerline are 
present, but the ones on the left don't. Pixel size 14, brings the reverse 
problem. Font size 13 seems to work just fine.
