*****************
How to contribute
*****************

So you want to contribute to the Powerline project? Awesome! This document 
describes the guidelines you should follow when making contributions to the 
project.

**Please note that these guidelines aren't mandatory in any way, but your 
pull request will be merged a lot faster if you follow them.**

Getting started
===============

* Make sure you have a `GitHub account <https://github.com/signup/free>`_.
* Submit an `issue on GitHub <https://github.com/powerline/powerline/issues>`_, 
  assuming one does not already exist.

  * Clearly describe the issue.
  * If the issue is a bug: make sure you include steps to reproduce, and 
    include the earliest revision that you know has the issue.

* Fork the repository on GitHub.

Making changes
==============

* Create a topic branch from where you want to base your work.

  * Powerline uses the `Git Flow 
    <http://nvie.com/posts/a-successful-git-branching-model/>`_ branching 
    model.
  * Most contributions should be based off the ``develop`` branch.
  * Prefix your branch with ``feature/`` if you're working on a new feature.
  * Include the issue number in your topic branch, e.g.  
    ``321-fix-some-error`` or ``feature/123-a-cool-feature``.

* Make commits of logical units.
* Run your code through ``flake8`` and fix any programming style errors. Use 
  common sense regarding whitespace warnings, not all warnings need to be 
  fixed.
* Make sure your commit messages are in the `proper format 
  <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.  
  The summary must be no longer than 70 characters. Refer to any related 
  issues with e.g. ``Ref #123`` or ``Fixes #234`` at the bottom of the 
  commit message. Commit messages can use Markdown with the following 
  exceptions:

  * No HTML extensions.
  * Only indented code blocks (no ``````` blocks).
  * Long links should be moved to the bottom if they make the text wrap or 
    extend past 72 columns.

* Make sure you have added the necessary tests for your changes.
* Run *all* the tests to assure nothing else was accidentally broken.

Programming style
-----------------

* The project uses *tabs for indentation* and *spaces for alignment*, this 
  is also included in a vim modeline on top of every script file.
* Run your code through ``flake8 --ignore=W191,E501,E128,W291,E126,E101`` to fix 
  any style errors. Use common sense regarding whitespace warnings, not all 
  ``flake8`` warnings need to be fixed.
* Trailing whitespace to indicate a continuing paragraph is OK in comments, 
  documentation and commit messages.
* It is allowed to have too long lines. It is advised though to avoid lines 
  wider then a hundred of characters.
* Imports have the following structure:

  1. Shebang and modeline in a form

     .. code-block:: python

         #!/usr/bin/env python
         # vim:fileencoding=utf-8:noet

     . Modeline is required, shebang is not. If shebang is present file must end 
     with

     .. code-block:: python

        if __name__ == '__main__':
            # Actual script here

  2. Module docstring.
  3. ``__future__`` import exactly in a form

     .. code-block:: python

         from __future__ import (unicode_literals, division, absolute_import, print_function)

     (powerline.shell is the only exception due to problems with argparse). It 
     is not separated by newline with shebang and modeline, but is with 
     docstring.
  4. Standard python library imports in a form ``import X``.
  5. Standard python library imports in a form ``from X import Y``.
  6. Third-party (non-python and non-powerline) library imports in a form 
     ``import X``.
  7. Third-party library imports in a form ``from X import Y``.
  8. Powerline non-test imports in a form ``from powerline.X import Y``.
  9. Powerline test imports in a form ``import tests.vim as vim_module``.
  10. Powerline test imports in a form ``from tests.X import Y``.

  Each entry is separated by newline from another entry. Any entry except for 
  the first and third ones is optional. Example with all entries:

  .. code-block:: python

    #!/usr/bin/env python
    # vim:fileencoding=utf-8:noet

    '''Powerline super module'''

    from __future__ import (unicode_literals, division, absolute_import, print_function)

    import sys

    from argparse import ArgumentParser

    import psutil

    from colormath.color_diff import delta_e_cie2000

    from powerline.lib.unicode import u

    import tests.vim as vim_module

    from tests import TestCase

Submitting changes
==================

* Push your changes to a topic branch in your fork of the repository.
* If necessary, use ``git rebase -i <revision>`` to squash or reword commits
  before submitting a pull request.
* Submit a pull request to `powerline repository 
  <https://github.com/powerline/powerline>`_.
