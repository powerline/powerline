************
Local themes
************

From the user point of view local themes are the regular themes with a specific 
scope where they are applied (i.e. specific vim window or specific kind of 
prompt). Used themes are defined in :ref:`local_themes key 
<config-ext-local_themes>`.

Vim local themes
================

Vim is the only available extension that has a wide variaty of options for local 
themes. It is the only extension where local theme key refers to a function as 
described in :ref:`local_themes value documentation <config-ext-local_themes>`. 

This function always takes a single value named ``matcher_info`` which is the 
same dictionary as :ref:`segment_info dictionary <dev-segment_info-vim>`. Unlike 
segments it takes this single argument as a *positional* argument, not as 
a keyword one.

Matcher function should return a boolean value: ``True`` if theme applies for 
the given ``matcher_info`` dictionary or ``False`` if it is not. When one of the 
matcher functions returns ``True`` powerline takes the corresponding theme at 
uses it for the given window. Matchers are not tested in any particular order.

In addition to :ref:`local_themes configuration key <config-ext-local_themes>` 
developer of some plugin which wishes to support powerline without including his 
code in powerline tree may use 
:py:meth:`powerline.vim.VimPowerline.add_local_theme` method. It accepts two 
arguments: matcher name (same as in :ref:`local_themes 
<config-ext-local_themes>`) and dictionary with theme. This dictionary is merged 
with :ref:`top theme <config-ext-top_theme>` and 
:file:`powerline/themes/vim/__main__.json`. Note that if user already specified 
the matcher in his configuration file ``KeyError`` is raised.

Other local themes
==================

Except for Vim only IPython and shells have local themes. Unlike Vim these 
themes are names with no special meaning (they do not refer to or cause loading 
of any Python functions):

+---------+------------+-------------------------------------------------------+
|Extension|Theme name  |Description                                            |
+---------+------------+-------------------------------------------------------+
|Shell    |continuation|Shown for unfinished command (unclosed quote,          |
|         |            |unfinished cycle).                                     |
|         +------------+-------------------------------------------------------+
|         |select      |Shown for ``select`` command available in some shells. |
+---------+------------+-------------------------------------------------------+
|IPython  |in2         |Continuation prompt: shown for unfinished (multiline)  |
|         |            |expression, unfinished class or function definition.   |
|         +------------+-------------------------------------------------------+
|         |out         |Displayed before the result.                           |
|         +------------+-------------------------------------------------------+
|         |rewrite     |Displayed before the actually executed code when       |
|         |            |``autorewrite`` IPython feature is enabled.            |
+---------+------------+-------------------------------------------------------+
