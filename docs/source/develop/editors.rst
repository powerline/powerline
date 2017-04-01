.. _dev-editors:

***************
Editor bindings
***************

Editor support code expects editor to have some kind of script programming 
language which may be used to obtain information about editor state. For common 
tasks :py:class:`powerline.editors.Editor` provides an abstraction which may be 
used to get necessary information: e.g. to state that segment needs currently 
open file name :py:func:`powerline.editors.with_input` should be used to 
decorate the segment like this: ``@with_input('buffer_name')``. This also uses
:py:func:`powerline.theme.requires_segment_info` decorator, requested 
information is made available through :ref:`the segment dictionary 
<dev-segments-segment>`, using ``input`` key: 
``segment_info['input']['buffer_name']``.

This, of course, works only for standard requests, see attributes of the 
:py:class:`powerline.editors.Editor` object (those whose description starts with 
“Definition of”). To get something non-standard, e.g. create a segment which is 
specific to a custom plugin then, it is needed to know how such “definitions of” 
are created.

The core part of “low-level” interaction with the editor is 
:py:class:`powerline.editors.EditorObj` class and its subclasses. This hierarchy 
is basically a representation of AST of some abstract language, which editor 
bindings then need to compile into actual code. This layer is needed to move 
some processing to the editor side: e.g. if a custom plugin dumps a big bunch of 
data into a state dictionary and statusline segment needs only a small portion 
of it it may construct code which will take only that small portion. Profitable 
if powerline lives in one process and editor in another, communicating via some 
IPC mechanism.

How :py:class:`powerline.editors.EditorObj`-based AST is converted into actual 
editor code is determined by :py:attr:`powerline.editors.Editor.edconverters`, 
used by :py:meth:`powerline.editors.Editor.toed`.

But what editor can transfer over the wire is sometimes limited: e.g. 
``vim.eval`` (from Vim editor) always represents numbers as strings. So 
additional layer is introduced: after information is received it is converted. 
Conversion happens by first determining type of the result via 
:py:attr:`powerline.editors.Editor.types` key which maps names of “definition 
of” attributes to their types (should be extended by subclasses), 
:py:attr:`powerline.editors.Editor.converters` are then responsible for 
converting result from whatever was received from the editor to what powerline 
segments expect.

.. _dev-editors-segments:

Segments with custom input
==========================

As noted earlier, to get data defined by one of “definition of” attributes of 
:py:class:`powerline.editors.Editor` one just provides attribute name to 
:py:func:`powerline.editors.with_input`. But if segment cannot use one of 
:py:class:`powerline.editors.Editor` attributes then 
:py:func:`powerline.editors.with_input` accepts different variant: 
``with_input((req_name, req_def, req_type))``. I.e. a 3-tuple with

#. Requirement name, string. Must be unique, requested data will appear in the 
   ``segment_info['input']`` dictionary with this key.
#. Requirement definition. Format is identical to 
   :py:class:`powerline.editors.Editor` “definition of” attributes format and is 
   editor-specific.
#. Requirement type, string. Should be a key of 
   :py:attr:`powerline.editors.Editor.converters` dictionary (or to the same 
   attribute of subclasses). If key is not present in the dictionary, it will 
   just be treated as “pass data as-is”.

These forms may be mixed: e.g. to get variable ``MyFooVar`` value alongside with 
the file name for the segment the following code may be used:

.. code-block:: python

   from powerline.editors.vim import VimGlobalVar
   from powerline.editors import with_input

   @with_input(
       'buffer_name',
       ('foo_my_var', (VimGlobalVar('MyFooVar'),), 'int'),
   )
   def foo(pl, segment_info):
       '''Segment which displays MyFooVar’th character of the buffer name
       '''
       bufname = segment_info['input']['buffer_name']
       return bufname[segment_info['input']['foo_my_var']]

.. _dev-editors-listers:

Lister segments
===============

One of the powerline features are :ref:`lister “segments” <dev-listers>`. They 
also require special support from editor code, specifically decorators must be 
marked with :py:func:`powerline.editors.with_list` (also applies 
:py:func:`powerline.themes.requires_segment_info`) which accepts a single 
argument a pair with

#. What is being iterated over, string: one of ``list_…`` 
   :py:attr:`powerline.editors.Editor.list_objects` (or subclasses) key names, 
   *with* prefix.
#. A tuple with additional requirements, used by the lister function itself. 
   Requirements the same format as :py:func:`powerline.editors.with_input` 
   arguments, see :ref:`editor segments description <dev-editors-segments>`.

Lister segment will receive in its ``segment_info`` dictionary, in ``input`` 
dictionary ``list_…_inputs`` (e.g. ``list_tabs_inputs``, 
``list_buffers_inputs``) lists with all the necessary data for the segments. 
“Additional requirements” are also present inside that list. Editor listers are 
supposed to return list with pairs with ``segment_info`` dictionaries with 
``input`` keys with contents copied from ``list_…_inputs`` list.

Editor bindings
===============

As all other bindings, editor bindings must define 
:py:class:`powerline.renderer.Renderer` and :py:class:`powerline.Powerline` 
subclasses. But additionally they need to subclass 
:py:class:`powerline.editors.Editor`. Responsibilities of renderer and powerline 
subclasses are described in :ref:`Creating new powerline extensions 
<dev-extensions>` document, but what makes editors special is that these 
responsibilities are partially implemented on top of 
:py:class:`powerline.editors.Editor` subclass which defines some interactions 
with the editor.

The main thing :py:class:`powerline.editors.Editor` produces is a requirements 
dictionary produced by :py:meth:`powerline.editors.Editor.reqs_to_reqs_dict`, 
normally used indirectly from 
:py:meth:`powerline.editors.Editor.theme_to_reqs_dict`. Dictionary returned by 
these methods is transformed by 
:py:meth:`powerline.editors.Editor.compile_reqs_dict` to some editor-specific 
code which is responsible for both obtaining requested data from the editor and 
converting it to the data types expected by the segments. Editor-specific 
:py:class:`powerline.Powerline` subclass is responsible for actually using the 
result of the compilation.

Additional entry point is 
:py:meth:`powerline.editors.Editor.compile_themes_getter`; this one is needed 
for matchers to work, again actual user of the compilation results should be 
:py:class:`powerline.Powerline` subclass.

powerline.editors module
========================

.. automodule:: powerline.editors
   :members:
