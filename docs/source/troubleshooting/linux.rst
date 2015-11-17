************************
Troubleshooting on Linux
************************

I can’t see any fancy symbols, what’s wrong?
--------------------------------------------

* Make sure that you’ve configured gvim or your terminal emulator to use 
  a patched font.
* You need to set your ``LANG`` and ``LC_*`` environment variables to 
  a UTF-8 locale (e.g. ``LANG=en_US.utf8``). Consult your Linux distro’s 
  documentation for information about setting these variables correctly.
* Make sure that vim is compiled with the ``--with-features=big`` flag.
* If you’re using rxvt-unicode make sure that it’s compiled with the 
  ``--enable-unicode3`` flag.
* If you’re using xterm make sure you have told it to work with unicode. You may 
  need ``-u8`` command-line argument, ``uxterm`` shell wrapper that is usually 
  shipped with xterm for this or ``xterm*utf8`` property set to ``1`` or ``2`` 
  in ``~/.Xresources`` (applied with ``xrdb``). Note that in case ``uxterm`` is 
  used configuration is done via ``uxterm*…`` properties and not ``xterm*…``.

  In any case the only absolute requirement is launching xterm with UTF-8 
  locale.
* If you are using bitmap font make sure that 
  :file:`/etc/fonts/conf.d/70-no-bitmaps.conf` does not exist. If it does check 
  out your distribution documentation to find a proper way to remove it (so that 
  it won’t reappear after update). E.g. in Gentoo this is::

      eselect fontconfig disable 70-no-bitmaps.conf

  (currently this only removes the symlink from :file:`/etc/fonts/conf.d`). Also 
  check out that no other fontconfig file does not have ``rejectfont`` tag that 
  tells fontconfig to disable bitmap fonts (they are referenced as not 
  scalable).

The fancy symbols look a bit blurry or “off”!
---------------------------------------------

* Make sure that you have patched all variants of your font (i.e. both the 
  regular and the bold font files).

I am seeing strange blocks in place of playing/paused/stopped signs
-------------------------------------------------------------------

If you are using ``powerline_unicode7`` :ref:`top-level theme 
<config-common-default_top_theme>` then symbols for player segments are taken 
from U+23F4–U+23FA range which is missing from most fonts. You may fix the issue 
by using `Symbola <http://users.teilar.gr/~g1951d/>`_ font (or any other font 
which contains these glyphs).

If your terminal emulator is using fontconfig library then you can create 
a fontconfig configuration file with the following contents:

.. code-block:: xml

    <?xml version="1.0"?>
    <!DOCTYPE fontconfig SYSTEM "fonts.dtd">

    <fontconfig>
    	<alias>
    		<family>Terminus</family>
    		<prefer><family>Symbola</family></prefer>
    	</alias>
    </fontconfig>

(replace ``Terminus`` with the name of the font you are using). Exact sequence 
of actions you need to perform is different across distributions, most likely it 
will work if you put the above xml into 
:file:`/etc/fonts/conf.d/99-prefer-symbola.conf`. On Gentoo you need to put it 
into :file:`/etc/fonts/conf.d/99-prefer-symbola.conf` and run::

    eselect fontconfig enable 99-prefer-symbola

.

.. warning::
    This answer is only applicable if you use ``powerline_unicode7`` theme or if 
    you configured powerline to use the same characters yourself.
