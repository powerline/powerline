**********************
Window manager widgets
**********************

Awesome widget
==============

.. note:: Powerline currently only supports awesome 3.5.

.. note:: The Powerline widget will spawn a shell script that runs in the 
   background and updates the statusline with ``awesome-client``.

Add the following to :file:`rc.lua`, where ``{repository_root}`` is the absolute 
path to Powerline installation directory (see :ref:`repository root 
<repository-root>`):

.. code-block:: lua

   package.path = package.path .. ';{repository_root}/powerline/bindings/awesome/?.lua'
   require('powerline')

Then add the ``powerline_widget`` to ``wibox``:

.. code-block:: lua

   right_layout:add(powerline_widget)

Qtile widget
============

Add the following to :file:`~/.config/qtile/config.py`:

.. code-block:: python

   from libqtile.bar import Bar
   from libqtile.config import Screen
   from libqtile.widget import Spacer

   from powerline.bindings.qtile.widget import PowerlineTextBox

   screens = [
       Screen(
           top=Bar([
                   PowerlineTextBox(update_interval=2, side='left'),
                   Spacer(),
                   PowerlineTextBox(update_interval=2, side='right'),
               ],
               35 # width
           ),
       ),
   ]

.. _bar-usage:

bar-aint-recursive
==================

To run the bar simply pipe the output of the binding script into ``bar`` and 
specify appropriate options, for example like this::

    python /path/to/powerline/bindings/bar/powerline-bar.py | bar

to run with i3, simply ``exec`` this in i3 config file::

    exec python /path/to/powerline/bindings/bar/powerline-bar.py --i3 | bar

Running the binding in i3-mode will require `i3ipc <https://github.com/acrisci/i3ipc-python>`_
(or the outdated `i3-py <https://github.com/ziberna/i3-py>`_).

See the `bar documentation <https://github.com/LemonBoy/bar>`_ for more 
information and options.

I3 bar
======

.. note::
   As the patch to include background-colors in i3bar is likely not to be 
   merged, it is recommended to instead run ``bar`` (see above). The source for 
   i3bgbar is however still available `here 
   <https://github.com/S0lll0s/i3bgbar>`_.

Add the following to :file:`~/.i3/config`::

    bar {
        i3bar_command i3bgbar

        status_command python /path/to/powerline/bindings/i3/powerline-i3.py
        font pango:PowerlineFont 12
    }

where ``i3bgbar`` may be replaced with the path to the custom i3bar binary and 
``PowerlineFont`` is any system font with powerline support.
