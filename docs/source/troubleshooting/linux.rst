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

The fancy symbols look a bit blurry or “off”!
---------------------------------------------

* Make sure that you have patched all variants of your font (i.e. both the 
  regular and the bold font files).
