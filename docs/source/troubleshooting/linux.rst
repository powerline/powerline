************************
Troubleshooting on Linux
************************

I can't see any fancy symbols, what's wrong?
--------------------------------------------

* Make sure that you've configured gvim or your terminal emulator to use 
  a patched font.
* You need to set your ``LANG`` and ``LC_*`` environment variables to 
  a UTF-8 locale (e.g. ``LANG=en_US.utf8``). Consult your Linux distro's 
  documentation for information about setting these variables correctly.
* Make sure that vim is compiled with the ``--with-features=big`` flag.
* If you're using rxvt-unicode, make sure that it's compiled with the 
  ``--enable-unicode3`` flag.

The fancy symbols look a bit blurry or "off"!
---------------------------------------------

* Make sure that you have patched all variants of your font (i.e. both the 
  regular and the bold font files).
