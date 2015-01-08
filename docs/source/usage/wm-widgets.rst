**********************
Window manager widgets
**********************

Awesome widget
==============

.. note:: Powerline currently only supports awesome 3.5.

.. note:: The Powerline widget will spawn a shell script that runs in the 
   background and updates the statusline with ``awesome-client``.

Add the following to your :file:`rc.lua`, where ``{repository_root}`` is the 
absolute path to your Powerline installation directory:

.. code-block:: lua

   package.path = package.path .. ';{repository_root}/powerline/bindings/awesome/?.lua'
   require('powerline')

Then add the ``powerline_widget`` to your ``wibox``:

.. code-block:: lua

   right_layout:add(powerline_widget)

Qtile widget
============

Add the following to your :file:`~/.config/qtile/config.py`:

.. code-block:: python

   from powerline.bindings.qtile.widget import Powerline

   screens = [
       Screen(
           top=bar.Bar([
                   # ...
                   Powerline(timeout=2),
                   # ...
               ],
           ),
       ),
   ]

.. _bar-usage:

bar
===

.. note:: There is currently only a script to run inside i3, but you can just strip the
          i3-specific parts of the binding.

To run the bar simply pipe the output of the binding script into ``bar`` and specify appropriate
options, for example like this::

    python powerline-bar.py | bar -f "-xos4-*-*-*-*-*-*-*-*-*-*-*-*-*

to run with i3, simply ``exec`` this in your i3 config file::

    exec python powerline-bar.py | bar -f "-xos4-*-*-*-*-*-*-*-*-*-*-*-*-*

See the `bar documentation <https://github.com/LemonBoy/bar>`_ for more information and options.

I3 bar
======

.. note:: As the patch to include background-colors in i3bar is likely not to be merged,
          it is recommended to instead run ``bar`` (see above).
          The source for i3bgbar is however still available `here <https://github.com/S0lll0s/i3bgbar>`_.

Add the following to your :file:`~/.i3/config`::

    bar {
        i3bar_command i3bgbar

        status_command python /path/to/powerline/bindings/i3/powerline-i3.py
        font pango:PowerlineFont 12
    }

where ``i3bgbar`` may be replaced with the path to the custom i3bar binary and 
``PowerlineFont`` is any system font with powerline support.
