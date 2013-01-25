.. _font-patching:

*************
Font patching
*************

Powerline provides a font patcher for custom glyphs like the segment 
dividers (arrows), branch symbol, padlock symbol, etc. The font patcher 
requires FontForge with Python bindings to work.

Check out the `powerline-fonts 
<https://github.com/Lokaltog/powerline-fonts>`_ repository on GitHub for 
patched versions of some popular programming fonts.

.. warning:: The code points have changed in this version of Powerline! This 
   means that you either have to patch your font again, or change the glyphs 
   Powerline uses in your user configuration.

.. note:: Powerline no longer works with rxvt-unicode unless you either use 
   rxvt-unicode compiled with ``--enable-unicode3``, or you use fonts patched 
   with the legacy font patcher and change the glyphs in your user 
   configuration.

Glyph table
===========

Powerline stores all special glyphs in the Unicode *Private Use Area* 
(``U+E000``-``U+F8FF``).

==========  =====  ===========
Code point  Glyph  Description
==========  =====  ===========
``U+E0A0``        Version control branch
``U+E0A1``        LN (line) symbol
``U+E0A2``        Closed padlock
``U+E0B0``        Rightwards black arrowhead
``U+E0B1``        Rightwards arrowhead
``U+E0B2``        Leftwards black arrowhead
``U+E0B3``        Leftwards arrowhead
==========  =====  ===========

Usage
=====

The font patcher is located at :file:`powerline/fontpatcher/fontpatcher.py`.  
It requires Python 2.7 and FontForge compiled with Python bindings to work.

Patched fonts are renamed by default (" for Powerline" is added to the font 
name) so they don't conflict with existing fonts. Use the ``--no-rename`` 
option to disable font renaming.

.. note:: Bitmap fonts are not supported, and will probably never be 
   supported officially due to difficulty creating a font patcher that works 
   for bitmap fonts. The recommended method of patching bitmap fonts is to draw 
   the glyphs manually using a tool like ``gbdfed``.

Linux
-----

1. Install fontforge with Python bindings. For Ubuntu users the required 
   package is ``python-fontforge``, for Arch Linux users the required 
   package is ``fontforge``. It should be something similar for other 
   distros.

2. Run the font patcher::

       $ /path/to/fontpatcher.py MyFontFile.ttf

3. Copy the font file into :file:`~/.fonts` (or another X font directory)::

       $ cp "MyFontFile for Powerline.otf" ~/.fonts

4. Update your font cache::

       $ fc-cache -vf ~/.fonts

   If you're using vim in a terminal you may need to close all open terminal 
   windows after updating the font cache.

5. **Gvim users:** Update the GUI font in your :file:`vimrc` file::

       set guifont=MyFont\ for\ Powerline

   **Terminal users:** Update your terminal configuration to use the patched 
   font.

6. Open vim and enjoy your new statusline!

OS X
----

1. Check if you have a FontForge version with Python support by running 
   ``fontforge -version``. You should see something like this::

       $ fontforge -version
       Copyright (c) 2000-2011 by George Williams.
       Executable based on sources from 13:48 GMT 22-Feb-2011-D.
       Library based on sources from 13:48 GMT 22-Feb-2011.
       fontforge 20110222
       libfontforge 20110222

   Make sure that the executable version number doesn't have ``NoPython`` in 
   it. If everything looks OK, skip ahead to step 4.

2. If you have FontForge but with ``NoPython`` in the version number, please 
   try to update to a later version::

       $ brew uninstall fontforge
       $ brew update
       $ brew install fontforge

   **Note:** You may have to use ``--use-clang`` instead of ``--use-gcc`` 
   when compiling FontForge.

3. If you don't have FontForge, install it with Homebrew::

       $ brew update
       $ brew install fontforge

4. Patch your fonts by passing the ``fontpatcher`` script as a parameter to 
   FontForge::

       $ fontforge -script /path/to/fontpatcher.py MyFontFile.ttf

5. Install the font by double-clicking the font file in Finder and click 
   "Install this font" from the preview window.

6. **Gvim users:** Update the GUI font in your :file:`vimrc` file::

       set guifont=MyFont\ for\ Powerline

   **Terminal users:** Update your terminal configuration to use the patched 
   font.

7. Open vim and enjoy your new statusline!
