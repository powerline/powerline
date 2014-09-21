.. _config-segments:

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
don’t provide an ``args`` dict.

More information is available in :ref:`Writing segments <dev-segments>` section.

Available segments
==================

.. toctree::
   :glob:

   segments/*
