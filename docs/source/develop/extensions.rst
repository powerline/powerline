********************************
Creating new powerline extension
********************************

Powerline extension is a code that tells powerline how to highlight and display 
segments in some set of applications. Specifically this means

#. Creating a :py:class:`powerline.Powerline` subclass that knows how to obtain 
   :ref:`local configuration overrides <local-configuration-overrides>`. It also 
   knows how to load local themes, but not when to apply them.

   Instance of this class is the only instance that interacts directly with 
   bindings code, so it has a proxy :py:meth:`powerline.Powerline.render` and 
   :py:meth:`powerline.Powerline.shutdown` methods and other methods which may 
   be useful for bindings.

   This subclass must be placed directly in :file:`powerline` directory (e.g. in 
   :file:`powerline/vim.py`) and named like ``VimPowerline`` (version of the 
   file name without directory and extension and first capital letter 
   + ``Powerline``). There is no technical reason for naming classes like this.
#. Creating a :py:class:`powerline.renderer.Renderer` subclass that knows how to 
   highlight a segment or reset highlighting to the default value (only makes 
   sense in prompts). It is also responsible for selecting local themes and 
   computing text width.

   This subclass must be placed directly in :file:`powerline/renderers` 
   directory (for powerline extensions developed for a set of applications use 
   :file:`powerline/renderers/{ext}/*.py`) and named like ``ExtRenderer`` or 
   ``AppPromptRenderer``. For technical reasons the class itself must be 
   referenced in ``renderer`` module attribute thus allowing only one renderer 
   per one module.
#. Creating an extension bindings. These are to be placed in 
   :file:`powerline/bindings/{ext}` and may contain virtually anything which may 
   be required for powerline to work inside given applications, assuming it does 
   not fit in other places.

Powerline class
===============

.. autoclass:: powerline.Powerline
   :members:

Renderer class
==============

.. autoclass:: powerline.renderer.Renderer
   :members:
