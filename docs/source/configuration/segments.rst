*****************
Segment reference
*****************

Segments
========

Segments are written in Python, and the default segments provided with 
Powerline are located in :file:`powerline/segments/{extension}.py`.  
User-defined segments can be defined in any module in ``sys.path`` or 
:ref:`paths common configuration option <config-common-paths>`, import is 
always absolute.

Segments are regular Python functions, and they may accept arguments. All 
arguments should have a default value which will be used for themes that 
don't provide an ``args`` dict.

A segment function must return one of the following values:

* ``None``, which will remove the segment from the prompt/statusline.
* A string, which will be the segment contents.
* A list of dicts consisting of a ``contents`` string, and 
  a ``highlight_group`` list. This is useful for providing a particular 
  highlighting group depending on the segment contents.

Available segments
==================

.. toctree::
   :glob:

   segments/*
